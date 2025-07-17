"""
Thin storage abstraction over AWS S3 (default) or local filesystem (dev fallback).

S3 is used when AWS credentials + bucket are configured.
Falls back to local ./uploads/ directory when storage_provider == "local"
or AWS creds are missing, so dev environments work without cloud credentials.
"""

import uuid
from pathlib import Path
from typing import BinaryIO

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

_LOCAL_UPLOAD_DIR = Path("uploads")


def _local_path(key: str) -> Path:
    path = _LOCAL_UPLOAD_DIR / key
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _s3_client():
    return boto3.client(
        "s3",
        region_name=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id or None,
        aws_secret_access_key=settings.aws_secret_access_key or None,
    )


def _use_s3() -> bool:
    return (
        settings.storage_provider == "s3"
        and bool(settings.aws_access_key_id)
        and bool(settings.aws_secret_access_key)
    )


def generate_storage_key(workspace_id: str, filename: str) -> str:
    """Return a deterministic, collision-safe S3 key / local path."""
    ext = Path(filename).suffix.lower()
    return f"workspaces/{workspace_id}/documents/{uuid.uuid4()}{ext}"


def upload_file(
    file_obj: BinaryIO,
    key: str,
    content_type: str,
) -> str:
    """
    Upload file_obj to S3 (or local disk).
    Returns the storage key on success.
    """
    if _use_s3():
        try:
            s3 = _s3_client()
            s3.upload_fileobj(
                file_obj,
                settings.aws_s3_bucket,
                key,
                ExtraArgs={"ContentType": content_type},
            )
            logger.info("Uploaded to S3", extra={"key": key})
            return key
        except (ClientError, NoCredentialsError) as exc:
            logger.error("S3 upload failed", extra={"key": key, "error": str(exc)})
            raise

    # Local fallback
    dest = _local_path(key)
    with open(dest, "wb") as f:
        f.write(file_obj.read())
    logger.info("Saved locally", extra={"path": str(dest)})
    return key


def delete_file(key: str) -> None:
    """Delete from S3 or local disk. Silently ignores missing files."""
    if _use_s3():
        try:
            _s3_client().delete_object(Bucket=settings.aws_s3_bucket, Key=key)
        except ClientError as exc:
            logger.warning("S3 delete failed", extra={"key": key, "error": str(exc)})
        return

    path = _local_path(key)
    if path.exists():
        path.unlink()


def get_presigned_url(key: str, expires_in: int = 3600) -> str:
    """
    Return a presigned URL (S3) or a local file path URL (dev).
    """
    if _use_s3():
        s3 = _s3_client()
        return s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.aws_s3_bucket, "Key": key},
            ExpiresIn=expires_in,
        )
    # Dev: just return a relative path served by a static mount
    return f"/uploads/{key}"


def download_file_bytes(key: str) -> bytes:
    """Download the entire file into memory. Used by Celery workers."""
    if _use_s3():
        s3 = _s3_client()
        obj = s3.get_object(Bucket=settings.aws_s3_bucket, Key=key)
        return obj["Body"].read()

    path = _local_path(key)
    return path.read_bytes()

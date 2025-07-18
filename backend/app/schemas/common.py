from typing import Any, Generic, TypeVar
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Base schema — enables ORM mode for all children
# ---------------------------------------------------------------------------

class AppSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Generic paginated response
# ---------------------------------------------------------------------------

class PaginatedResponse(AppSchema, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class PaginationParams(BaseModel):
    page: int = 1
    page_size: int = 20

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


# ---------------------------------------------------------------------------
# Standard API response wrappers
# ---------------------------------------------------------------------------

class MessageResponse(BaseModel):
    message: str


class ErrorDetail(BaseModel):
    code: str
    message: str
    field: str | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class DataResponse(BaseModel, Generic[T]):
    data: T


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    status: str
    environment: str

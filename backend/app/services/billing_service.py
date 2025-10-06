import uuid
from datetime import datetime

import stripe
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.billing import Subscription, UsageLog
from app.models.document import Document
from app.schemas.billing import PLANS, PlanInfo, UsageStats
from app.utils.exceptions import NotFoundError, ValidationError

stripe.api_key = settings.stripe_secret_key

PRICE_TO_TIER = {
    settings.stripe_price_pro: "pro",
    settings.stripe_price_team: "team",
}
TIER_TO_PRICE = {
    "pro": settings.stripe_price_pro,
    "team": settings.stripe_price_team,
}


# ---------------------------------------------------------------------------
# Subscription helpers
# ---------------------------------------------------------------------------

async def get_or_create_subscription(
    db: AsyncSession, workspace_id: uuid.UUID
) -> Subscription:
    result = await db.execute(
        select(Subscription).where(Subscription.workspace_id == workspace_id)
    )
    sub = result.scalar_one_or_none()
    if sub:
        return sub
    sub = Subscription(workspace_id=workspace_id, plan_tier="free", status="active")
    db.add(sub)
    await db.flush()
    return sub


async def get_subscription(db: AsyncSession, workspace_id: uuid.UUID) -> Subscription:
    result = await db.execute(
        select(Subscription).where(Subscription.workspace_id == workspace_id)
    )
    sub = result.scalar_one_or_none()
    if not sub:
        return await get_or_create_subscription(db, workspace_id)
    return sub


def get_plan(tier: str) -> PlanInfo:
    plan = PLANS.get(tier)
    if not plan:
        raise ValidationError(f"Unknown plan tier: {tier}")
    return plan


# ---------------------------------------------------------------------------
# Stripe checkout
# ---------------------------------------------------------------------------

async def create_checkout_session(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    user_email: str,
    plan_tier: str,
    success_url: str,
    cancel_url: str,
) -> str:
    if plan_tier not in TIER_TO_PRICE:
        raise ValidationError(f"Cannot checkout for tier: {plan_tier}")

    sub = await get_or_create_subscription(db, workspace_id)

    # Create or reuse Stripe customer
    if not sub.stripe_customer_id:
        customer = stripe.Customer.create(
            email=user_email,
            metadata={"workspace_id": str(workspace_id)},
        )
        sub.stripe_customer_id = customer.id
        await db.flush()

    session = stripe.checkout.Session.create(
        customer=sub.stripe_customer_id,
        mode="subscription",
        line_items=[{"price": TIER_TO_PRICE[plan_tier], "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"workspace_id": str(workspace_id)},
    )
    return session.url


# ---------------------------------------------------------------------------
# Stripe customer portal
# ---------------------------------------------------------------------------

async def create_portal_session(
    db: AsyncSession, workspace_id: uuid.UUID, return_url: str
) -> str:
    sub = await get_subscription(db, workspace_id)
    if not sub.stripe_customer_id:
        raise ValidationError("No billing account found. Please subscribe first.")
    session = stripe.billing_portal.Session.create(
        customer=sub.stripe_customer_id,
        return_url=return_url,
    )
    return session.url


# ---------------------------------------------------------------------------
# Webhook handlers
# ---------------------------------------------------------------------------

async def handle_checkout_completed(db: AsyncSession, session_obj: dict) -> None:
    workspace_id = session_obj.get("metadata", {}).get("workspace_id")
    stripe_sub_id = session_obj.get("subscription")
    stripe_customer_id = session_obj.get("customer")
    if not workspace_id or not stripe_sub_id:
        return

    sub = await get_or_create_subscription(db, uuid.UUID(workspace_id))
    sub.stripe_subscription_id = stripe_sub_id
    sub.stripe_customer_id = stripe_customer_id

    # Fetch subscription details from Stripe
    stripe_sub = stripe.Subscription.retrieve(stripe_sub_id)
    price_id = stripe_sub["items"]["data"][0]["price"]["id"]
    sub.plan_tier = PRICE_TO_TIER.get(price_id, "pro")
    sub.status = stripe_sub["status"]
    sub.stripe_price_id = price_id
    sub.current_period_start = datetime.fromtimestamp(stripe_sub["current_period_start"])
    sub.current_period_end = datetime.fromtimestamp(stripe_sub["current_period_end"])
    sub.updated_at = datetime.utcnow()
    await db.flush()


async def handle_subscription_updated(db: AsyncSession, stripe_sub: dict) -> None:
    sub_id = stripe_sub.get("id")
    result = await db.execute(
        select(Subscription).where(Subscription.stripe_subscription_id == sub_id)
    )
    sub = result.scalar_one_or_none()
    if not sub:
        return

    price_id = stripe_sub["items"]["data"][0]["price"]["id"]
    sub.plan_tier = PRICE_TO_TIER.get(price_id, sub.plan_tier)
    sub.status = stripe_sub["status"]
    sub.stripe_price_id = price_id
    sub.current_period_start = datetime.fromtimestamp(stripe_sub["current_period_start"])
    sub.current_period_end = datetime.fromtimestamp(stripe_sub["current_period_end"])
    sub.cancel_at_period_end = stripe_sub.get("cancel_at_period_end", False)
    sub.updated_at = datetime.utcnow()
    await db.flush()


async def handle_subscription_deleted(db: AsyncSession, stripe_sub: dict) -> None:
    sub_id = stripe_sub.get("id")
    result = await db.execute(
        select(Subscription).where(Subscription.stripe_subscription_id == sub_id)
    )
    sub = result.scalar_one_or_none()
    if not sub:
        return
    sub.plan_tier = "free"
    sub.status = "canceled"
    sub.stripe_subscription_id = None
    sub.stripe_price_id = None
    sub.current_period_start = None
    sub.current_period_end = None
    sub.cancel_at_period_end = False
    sub.updated_at = datetime.utcnow()
    await db.flush()


# ---------------------------------------------------------------------------
# Usage tracking
# ---------------------------------------------------------------------------

async def log_usage(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID | None,
    usage_type: str,
    tokens_used: int = 0,
) -> None:
    log = UsageLog(
        workspace_id=workspace_id,
        user_id=user_id,
        usage_type=usage_type,
        tokens_used=tokens_used,
    )
    db.add(log)
    await db.flush()


async def get_usage_stats(
    db: AsyncSession, workspace_id: uuid.UUID
) -> UsageStats:
    sub = await get_subscription(db, workspace_id)
    plan = get_plan(sub.plan_tier)

    # Count queries this period
    period_filter = []
    if sub.current_period_start:
        period_filter.append(UsageLog.created_at >= sub.current_period_start)

    query_count_q = select(func.count(UsageLog.id)).where(
        UsageLog.workspace_id == workspace_id,
        UsageLog.usage_type == "query",
        *period_filter,
    )
    query_count = (await db.execute(query_count_q)).scalar() or 0

    doc_count_q = select(func.count(Document.id)).where(
        Document.workspace_id == workspace_id
    )
    doc_count = (await db.execute(doc_count_q)).scalar() or 0

    return UsageStats(
        queries_used=query_count,
        queries_limit=plan.query_limit,
        documents_used=doc_count,
        documents_limit=plan.document_limit,
        period_start=sub.current_period_start,
        period_end=sub.current_period_end,
    )


async def check_query_quota(
    db: AsyncSession, workspace_id: uuid.UUID
) -> None:
    """Raises QuotaExceededError if workspace has exceeded query limit."""
    from app.utils.exceptions import QuotaExceededError

    stats = await get_usage_stats(db, workspace_id)
    if stats.queries_used >= stats.queries_limit:
        raise QuotaExceededError("queries")


async def check_document_quota(
    db: AsyncSession, workspace_id: uuid.UUID
) -> None:
    from app.utils.exceptions import QuotaExceededError

    stats = await get_usage_stats(db, workspace_id)
    if stats.documents_used >= stats.documents_limit:
        raise QuotaExceededError("documents")

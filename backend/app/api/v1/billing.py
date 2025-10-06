import logging

import stripe
from fastapi import APIRouter, Header, Request

from app.config import settings
from app.dependencies import CurrentUser, DbSession
from app.schemas.billing import (
    PLANS,
    CheckoutResponse,
    CreateCheckoutRequest,
    PlanInfo,
    PortalResponse,
    SubscriptionResponse,
    UsageStats,
)
from app.services import billing_service as svc
from app.utils.exceptions import ValidationError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["billing"])


# ---------------------------------------------------------------------------
# Plans
# ---------------------------------------------------------------------------

@router.get("/plans", response_model=list[PlanInfo])
async def list_plans():
    return list(PLANS.values())


# ---------------------------------------------------------------------------
# Subscription
# ---------------------------------------------------------------------------

@router.get(
    "/workspaces/{workspace_id}/subscription",
    response_model=SubscriptionResponse,
)
async def get_subscription(workspace_id: str, db: DbSession, user: CurrentUser):
    import uuid
    sub = await svc.get_or_create_subscription(db, uuid.UUID(workspace_id))
    await db.commit()
    return sub


# ---------------------------------------------------------------------------
# Checkout
# ---------------------------------------------------------------------------

@router.post(
    "/workspaces/{workspace_id}/checkout",
    response_model=CheckoutResponse,
)
async def create_checkout(
    workspace_id: str,
    body: CreateCheckoutRequest,
    db: DbSession,
    user: CurrentUser,
):
    import uuid
    url = await svc.create_checkout_session(
        db,
        uuid.UUID(workspace_id),
        user.email,
        body.plan_tier,
        body.success_url,
        body.cancel_url,
    )
    await db.commit()
    return CheckoutResponse(checkout_url=url)


# ---------------------------------------------------------------------------
# Portal
# ---------------------------------------------------------------------------

@router.post(
    "/workspaces/{workspace_id}/portal",
    response_model=PortalResponse,
)
async def create_portal(
    workspace_id: str,
    db: DbSession,
    user: CurrentUser,
):
    import uuid
    url = await svc.create_portal_session(
        db, uuid.UUID(workspace_id), f"{settings.frontend_url}/billing"
    )
    return PortalResponse(portal_url=url)


# ---------------------------------------------------------------------------
# Usage
# ---------------------------------------------------------------------------

@router.get(
    "/workspaces/{workspace_id}/usage",
    response_model=UsageStats,
)
async def get_usage(workspace_id: str, db: DbSession, user: CurrentUser):
    import uuid
    return await svc.get_usage_stats(db, uuid.UUID(workspace_id))


# ---------------------------------------------------------------------------
# Stripe Webhook
# ---------------------------------------------------------------------------

@router.post("/webhook/stripe")
async def stripe_webhook(
    request: Request,
    db: DbSession,
    stripe_signature: str = Header(alias="stripe-signature"),
):
    payload = await request.body()
    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, settings.stripe_webhook_secret
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        raise ValidationError("Invalid webhook signature")

    event_type = event["type"]
    data_obj = event["data"]["object"]

    if event_type == "checkout.session.completed":
        await svc.handle_checkout_completed(db, data_obj)
    elif event_type == "customer.subscription.updated":
        await svc.handle_subscription_updated(db, data_obj)
    elif event_type == "customer.subscription.deleted":
        await svc.handle_subscription_deleted(db, data_obj)
    else:
        logger.debug("Unhandled Stripe event: %s", event_type)

    await db.commit()
    return {"received": True}

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import AppSchema


# ---------------------------------------------------------------------------
# Plan definitions
# ---------------------------------------------------------------------------

class PlanInfo(BaseModel):
    tier: str
    name: str
    price_monthly: float
    query_limit: int
    document_limit: int
    members_limit: int
    features: list[str]


PLANS: dict[str, PlanInfo] = {
    "free": PlanInfo(
        tier="free", name="Free", price_monthly=0,
        query_limit=50, document_limit=10, members_limit=1,
        features=["Basic RAG chat", "PDF/TXT upload"],
    ),
    "pro": PlanInfo(
        tier="pro", name="Pro", price_monthly=29,
        query_limit=1000, document_limit=100, members_limit=5,
        features=["All file types", "URL scraping", "Priority support"],
    ),
    "team": PlanInfo(
        tier="team", name="Team", price_monthly=79,
        query_limit=5000, document_limit=500, members_limit=25,
        features=["Everything in Pro", "API access", "Embeddable widget", "Admin dashboard"],
    ),
}


# ---------------------------------------------------------------------------
# Subscription schemas
# ---------------------------------------------------------------------------

class SubscriptionResponse(AppSchema):
    id: uuid.UUID
    workspace_id: uuid.UUID
    plan_tier: str
    status: str
    stripe_subscription_id: str | None = None
    current_period_start: datetime | None = None
    current_period_end: datetime | None = None
    cancel_at_period_end: bool = False
    created_at: datetime
    updated_at: datetime


class CreateCheckoutRequest(BaseModel):
    plan_tier: str  # pro | team
    success_url: str
    cancel_url: str


class CheckoutResponse(BaseModel):
    checkout_url: str


class PortalResponse(BaseModel):
    portal_url: str


# ---------------------------------------------------------------------------
# Usage schemas
# ---------------------------------------------------------------------------

class UsageStats(BaseModel):
    queries_used: int
    queries_limit: int
    documents_used: int
    documents_limit: int
    period_start: datetime | None = None
    period_end: datetime | None = None


class UsageLogResponse(AppSchema):
    id: uuid.UUID
    usage_type: str
    tokens_used: int
    created_at: datetime

"""
Stripe Payment Integration Module
Handles checkout sessions and webhooks for subscriptions.
"""

import os
import logging
import asyncio
from datetime import datetime, timezone
from typing import Optional, Dict, Any

import stripe
from fastapi import APIRouter, HTTPException, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from utils.supabase_client import get_supabase_client
from utils.redis_client import cache_get, cache_set, cache_delete
from supabase import create_client, Client

def get_service_client() -> Optional[Client]:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        return None
    return create_client(url, key)

SESSION_COOKIE_NAME = "roboto_session"

# Configure logging
logger = logging.getLogger(__name__)

ERR_DB_UNAVAILABLE = "Database unavailable"
ERR_STRIPE_NOT_CONFIGURED = "Stripe not configured"

router = APIRouter()

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
logger.debug("Stripe initialized: secret key configured=%s", bool(stripe.api_key))


async def run_supabase_async(func):
    """Run sync Supabase operation in a thread."""
    return await asyncio.to_thread(func)


async def get_authenticated_user(request: Request) -> Dict[str, Any]:
    supabase = get_supabase_client()
    if not supabase:
        raise HTTPException(status_code=503, detail="Database unavailable")

    sess_id = request.cookies.get(SESSION_COOKIE_NAME)
    if not sess_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    now = datetime.now(timezone.utc).isoformat()
    session_result = await run_supabase_async(
        lambda: supabase.table("auth_sessions").select("user_id").eq("id", sess_id).gte("expires_at", now).execute()
    )
    if not session_result.data:
        raise HTTPException(status_code=401, detail="Session expired")

    user_id = session_result.data[0]["user_id"]
    user_result = await run_supabase_async(lambda: supabase.table("users").select("*").eq("id", user_id).execute())
    if not user_result.data:
        raise HTTPException(status_code=401, detail="User not found")

    return user_result.data[0]


async def upsert_subscription(
    supabase: Client,
    user_id: str,
    stripe_customer_id: Optional[str],
    stripe_subscription_id: Optional[str],
    status: str,
    tier: str,
    current_period_start: Optional[int],
    current_period_end: Optional[int],
    cancel_at_period_end: bool,
    trial_end: Optional[int],
) -> Dict[str, Any]:
    data = {
        "user_id": user_id,
        "stripe_customer_id": stripe_customer_id,
        "stripe_subscription_id": stripe_subscription_id,
        "status": status,
        "tier": tier,
        "current_period_start": datetime.fromtimestamp(current_period_start, tz=timezone.utc).isoformat() if current_period_start else None,
        "current_period_end": datetime.fromtimestamp(current_period_end, tz=timezone.utc).isoformat() if current_period_end else None,
        "cancel_at_period_end": cancel_at_period_end,
        "trial_end": datetime.fromtimestamp(trial_end, tz=timezone.utc).isoformat() if trial_end else None,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    result = await run_supabase_async(lambda: supabase.table("subscriptions").upsert(data).execute())
    return result.data[0] if result.data else data


class CheckoutRequest(BaseModel):
    price_id: Optional[str] = None
    success_url: str
    cancel_url: str


class PortalRequest(BaseModel):
    return_url: str


class CancelRequest(BaseModel):
    reason: Optional[str] = None


@router.post("/api/create-checkout-session", tags=["Payments"])
async def create_checkout_session(req: CheckoutRequest, request: Request):
    """Create a Stripe Checkout Session for subscription."""
    if not stripe.api_key:
        raise HTTPException(status_code=500, detail=ERR_STRIPE_NOT_CONFIGURED)

    supabase = get_supabase_client()
    if not supabase:
        raise HTTPException(status_code=503, detail=ERR_DB_UNAVAILABLE)

    user = await get_authenticated_user(request)
    user_id = user["id"]
    user_email = user.get("email")

    subscription_res = await run_supabase_async(
        lambda: supabase.table("subscriptions").select("stripe_customer_id").eq("user_id", user_id).execute()
    )
    stripe_customer_id = None
    if subscription_res.data:
        stripe_customer_id = subscription_res.data[0].get("stripe_customer_id")

    price_id = req.price_id or os.getenv("STRIPE_PRICE_ID_PREMIUM") or os.getenv("STRIPE_PRICE_ID")
    if not price_id:
        raise HTTPException(status_code=400, detail="Price ID not configured")

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price": price_id,
                    "quantity": 1,
                },
            ],
            mode="subscription",
            success_url=req.success_url,
            cancel_url=req.cancel_url,
            customer=stripe_customer_id,
            customer_email=None if stripe_customer_id else user_email,
            client_reference_id=user_id,
            metadata={
                "user_id": user_id
            }
        )
        return {"sessionId": checkout_session.id, "url": checkout_session.url}
    except Exception as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


async def _get_subscription_record(supabase: Client, user_id: str) -> Optional[Dict[str, Any]]:
    result = await run_supabase_async(
        lambda: supabase.table("subscriptions").select("*").eq("user_id", user_id).execute()
    )
    return result.data[0] if result.data else None


async def _log_subscription_event(
    supabase: Client,
    subscription_id: Optional[str],
    user_id: str,
    event_type: str,
    from_status: Optional[str],
    to_status: Optional[str],
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    try:
        await run_supabase_async(
            lambda: supabase.table("subscription_events").insert({
                "subscription_id": subscription_id,
                "user_id": user_id,
                "event_type": event_type,
                "from_status": from_status,
                "to_status": to_status,
                "metadata": metadata or {},
            }).execute()
        )
    except Exception as exc:
        logger.warning(f"Failed to log subscription event: {exc}")


@router.post("/api/create-portal-session", tags=["Payments"])
async def create_portal_session(req: PortalRequest, request: Request):
    if not stripe.api_key:
        raise HTTPException(status_code=500, detail=ERR_STRIPE_NOT_CONFIGURED)

    supabase = get_supabase_client()
    if not supabase:
        raise HTTPException(status_code=503, detail=ERR_DB_UNAVAILABLE)

    user = await get_authenticated_user(request)
    subscription = await _get_subscription_record(supabase, user["id"])
    customer_id = subscription.get("stripe_customer_id") if subscription else None
    if not customer_id:
        raise HTTPException(status_code=400, detail="No Stripe customer found")

    portal_config = os.getenv("STRIPE_PORTAL_CONFIG_ID")
    portal_args = {
        "customer": customer_id,
        "return_url": req.return_url,
    }
    if portal_config:
        portal_args["configuration"] = portal_config

    session = stripe.billing_portal.Session.create(**portal_args)
    return {"url": session.url}


@router.get("/api/subscription/status", tags=["Payments"])
async def get_subscription_status(request: Request):
    supabase = get_supabase_client()
    if not supabase:
        raise HTTPException(status_code=503, detail=ERR_DB_UNAVAILABLE)

    user = await get_authenticated_user(request)
    cache_key = f"subscription:{user['id']}"
    cached = await cache_get(cache_key)
    if cached:
        cached["cached"] = True
        return cached

    subscription = await _get_subscription_record(supabase, user["id"])
    response = {
        "success": True,
        "subscription": subscription or {"status": "inactive", "tier": "free"},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    await cache_set(cache_key, response, ttl=600)
    return response


@router.post("/api/subscription/cancel", tags=["Payments"])
async def cancel_subscription(req: CancelRequest, request: Request):
    if not stripe.api_key:
        raise HTTPException(status_code=500, detail=ERR_STRIPE_NOT_CONFIGURED)

    supabase = get_supabase_client()
    if not supabase:
        raise HTTPException(status_code=503, detail=ERR_DB_UNAVAILABLE)

    user = await get_authenticated_user(request)
    subscription = await _get_subscription_record(supabase, user["id"])
    if not subscription or not subscription.get("stripe_subscription_id"):
        raise HTTPException(status_code=404, detail="No active subscription")

    stripe_sub = stripe.Subscription.modify(
        subscription["stripe_subscription_id"],
        cancel_at_period_end=True,
    )

    await upsert_subscription(
        supabase,
        user["id"],
        stripe_sub.get("customer"),
        stripe_sub.get("id"),
        stripe_sub.get("status"),
        subscription.get("tier", "premium"),
        stripe_sub.get("current_period_start"),
        stripe_sub.get("current_period_end"),
        stripe_sub.get("cancel_at_period_end", False),
        stripe_sub.get("trial_end"),
    )

    await _log_subscription_event(
        supabase,
        subscription.get("id"),
        user["id"],
        "canceled",
        subscription.get("status"),
        stripe_sub.get("status"),
        {"reason": req.reason},
    )

    await cache_delete(f"subscription:{user['id']}")
    return {"success": True, "status": stripe_sub.get("status")}


@router.post("/api/subscription/reactivate", tags=["Payments"])
async def reactivate_subscription(request: Request):
    if not stripe.api_key:
        raise HTTPException(status_code=500, detail=ERR_STRIPE_NOT_CONFIGURED)

    supabase = get_supabase_client()
    if not supabase:
        raise HTTPException(status_code=503, detail=ERR_DB_UNAVAILABLE)

    user = await get_authenticated_user(request)
    subscription = await _get_subscription_record(supabase, user["id"])
    if not subscription or not subscription.get("stripe_subscription_id"):
        raise HTTPException(status_code=404, detail="No active subscription")

    stripe_sub = stripe.Subscription.modify(
        subscription["stripe_subscription_id"],
        cancel_at_period_end=False,
    )

    await upsert_subscription(
        supabase,
        user["id"],
        stripe_sub.get("customer"),
        stripe_sub.get("id"),
        stripe_sub.get("status"),
        subscription.get("tier", "premium"),
        stripe_sub.get("current_period_start"),
        stripe_sub.get("current_period_end"),
        stripe_sub.get("cancel_at_period_end", False),
        stripe_sub.get("trial_end"),
    )

    await _log_subscription_event(
        supabase,
        subscription.get("id"),
        user["id"],
        "reactivated",
        subscription.get("status"),
        stripe_sub.get("status"),
        None,
    )

    await cache_delete(f"subscription:{user['id']}")
    return {"success": True, "status": stripe_sub.get("status")}


@router.post("/api/stripe-webhook", tags=["Payments"])
async def stripe_webhook(request: Request, stripe_signature: str = Header(None)):
    """Handle Stripe webhooks."""
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    payload = await request.body()

    if not webhook_secret:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")

    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, webhook_secret
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_type = event["type"]
    obj = event["data"]["object"]

    if event_type == "checkout.session.completed":
        await handle_checkout_completed(obj)
    elif event_type in {"customer.subscription.created", "customer.subscription.updated"}:
        await handle_subscription_updated(obj, event_type)
    elif event_type == "customer.subscription.deleted":
        await handle_subscription_deleted(obj)
    elif event_type == "invoice.payment_succeeded":
        await handle_invoice_event(obj, "payment_succeeded")
    elif event_type == "invoice.payment_failed":
        await handle_invoice_event(obj, "payment_failed")

    return JSONResponse(content={"status": "success"})


async def handle_checkout_completed(session: Dict[str, Any]) -> None:
    """Activate subscription for user."""
    user_id = session.get("client_reference_id") or session.get("metadata", {}).get("user_id")
    subscription_id = session.get("subscription")
    customer_id = session.get("customer")

    if not user_id:
        logger.error("No user_id found in session")
        return

    supabase = get_service_client() or get_supabase_client()
    if not supabase:
        logger.error("Supabase not available for webhook")
        return

    stripe_subscription = stripe.Subscription.retrieve(subscription_id) if subscription_id else None
    status = stripe_subscription.get("status") if stripe_subscription else "active"
    tier = session.get("metadata", {}).get("tier", "premium")

    await upsert_subscription(
        supabase,
        user_id,
        customer_id,
        subscription_id,
        status,
        tier,
        stripe_subscription.get("current_period_start") if stripe_subscription else None,
        stripe_subscription.get("current_period_end") if stripe_subscription else None,
        stripe_subscription.get("cancel_at_period_end", False) if stripe_subscription else False,
        stripe_subscription.get("trial_end") if stripe_subscription else None,
    )

    await run_supabase_async(
        lambda: supabase.table("users").update({
            "subscription_status": status,
            "stripe_customer_id": customer_id,
            "subscription_id": subscription_id,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", user_id).execute()
    )

    await cache_delete(f"subscription:{user_id}")

    await _log_subscription_event(supabase, None, user_id, "activated", None, status, {"source": "checkout"})


async def handle_subscription_updated(subscription: Dict[str, Any], event_type: str) -> None:
    customer_id = subscription.get("customer")
    supabase = get_service_client() or get_supabase_client()
    if not supabase or not customer_id:
        return

    sub_res = await run_supabase_async(
        lambda: supabase.table("subscriptions").select("*").eq("stripe_customer_id", customer_id).execute()
    )
    existing = sub_res.data[0] if sub_res.data else None
    user_id = existing.get("user_id") if existing else None
    if not user_id:
        return

    updated = await upsert_subscription(
        supabase,
        user_id,
        customer_id,
        subscription.get("id"),
        subscription.get("status"),
        existing.get("tier", "premium") if existing else "premium",
        subscription.get("current_period_start"),
        subscription.get("current_period_end"),
        subscription.get("cancel_at_period_end", False),
        subscription.get("trial_end"),
    )

    await run_supabase_async(
        lambda: supabase.table("users").update({
            "subscription_status": updated.get("status"),
            "stripe_customer_id": customer_id,
            "subscription_id": updated.get("stripe_subscription_id"),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", user_id).execute()
    )

    log_event_type = "activated"
    if existing:
        if existing.get("status") == "canceled" and updated.get("status") == "active":
            log_event_type = "reactivated"
        elif existing.get("tier") and updated.get("tier") and existing.get("tier") != updated.get("tier"):
            log_event_type = "upgraded"

    await _log_subscription_event(
        supabase,
        updated.get("id"),
        user_id,
        log_event_type,
        existing.get("status") if existing else None,
        updated.get("status"),
        {"event": event_type},
    )

    await cache_delete(f"subscription:{user_id}")


async def handle_subscription_deleted(subscription: Dict[str, Any]) -> None:
    customer_id = subscription.get("customer")
    supabase = get_service_client() or get_supabase_client()
    if not supabase or not customer_id:
        return

    sub_res = await run_supabase_async(
        lambda: supabase.table("subscriptions").select("*").eq("stripe_customer_id", customer_id).execute()
    )
    existing = sub_res.data[0] if sub_res.data else None
    if not existing:
        logger.warning(f"No subscription found for customer {customer_id}")
        return

    await upsert_subscription(
        supabase,
        existing["user_id"],
        customer_id,
        subscription.get("id"),
        "canceled",
        existing.get("tier", "premium"),
        subscription.get("current_period_start"),
        subscription.get("current_period_end"),
        subscription.get("cancel_at_period_end", False),
        subscription.get("trial_end"),
    )

    await run_supabase_async(
        lambda: supabase.table("users").update({
            "subscription_status": "inactive",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", existing["user_id"]).execute()
    )

    await _log_subscription_event(
        supabase,
        existing.get("id"),
        existing["user_id"],
        "canceled",
        existing.get("status"),
        "canceled",
        None,
    )

    await cache_delete(f"subscription:{existing['user_id']}")


async def handle_invoice_event(invoice: Dict[str, Any], event_type: str) -> None:
    customer_id = invoice.get("customer")
    supabase = get_service_client() or get_supabase_client()
    if not supabase or not customer_id:
        return

    sub_res = await run_supabase_async(
        lambda: supabase.table("subscriptions").select("*").eq("stripe_customer_id", customer_id).execute()
    )
    existing = sub_res.data[0] if sub_res.data else None
    if not existing:
        return

    await _log_subscription_event(
        supabase,
        existing.get("id"),
        existing["user_id"],
        event_type,
        existing.get("status"),
        existing.get("status"),
        {"invoice_id": invoice.get("id")},
    )

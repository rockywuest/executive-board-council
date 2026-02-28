"""
Stripe Billing Integration for Executive Board Council.

Handles subscription management, checkout sessions, and webhooks.
"""

import os
from typing import Optional
import stripe
from fastapi import HTTPException, status, Request

from backend.auth import update_user_tier, UserTier


# ============================================================================
# Configuration
# ============================================================================

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PRICE_PRO_MONTHLY = os.getenv("STRIPE_PRICE_PRO_MONTHLY", "")
STRIPE_PRICE_PRO_YEARLY = os.getenv("STRIPE_PRICE_PRO_YEARLY", "")
STRIPE_PRICE_ENTERPRISE_MONTHLY = os.getenv("STRIPE_PRICE_ENTERPRISE_MONTHLY", "")

# Frontend URLs for redirects
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
SUCCESS_URL = f"{FRONTEND_URL}?payment=success"
CANCEL_URL = f"{FRONTEND_URL}?payment=cancelled"

# Initialize Stripe
if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY


# ============================================================================
# Helper Functions
# ============================================================================

def is_stripe_configured() -> bool:
    """Check if Stripe is properly configured."""
    return bool(STRIPE_SECRET_KEY and STRIPE_PRICE_PRO_MONTHLY)


def get_price_id(tier: str, interval: str = "monthly") -> Optional[str]:
    """
    Get Stripe price ID for a tier and billing interval.

    Args:
        tier: The tier (pro, enterprise)
        interval: Billing interval (monthly, yearly)

    Returns:
        Stripe price ID or None
    """
    if tier == "pro":
        return STRIPE_PRICE_PRO_YEARLY if interval == "yearly" else STRIPE_PRICE_PRO_MONTHLY
    elif tier == "enterprise":
        return STRIPE_PRICE_ENTERPRISE_MONTHLY
    return None


def tier_from_price_id(price_id: str) -> str:
    """
    Determine tier from Stripe price ID.

    Args:
        price_id: Stripe price ID

    Returns:
        Tier name (pro, enterprise, free)
    """
    if price_id in [STRIPE_PRICE_PRO_MONTHLY, STRIPE_PRICE_PRO_YEARLY]:
        return UserTier.PRO
    elif price_id == STRIPE_PRICE_ENTERPRISE_MONTHLY:
        return UserTier.ENTERPRISE
    return UserTier.FREE


# ============================================================================
# Checkout Functions
# ============================================================================

async def create_checkout_session(
    user_id: str,
    email: str,
    tier: str = "pro",
    interval: str = "monthly"
) -> str:
    """
    Create a Stripe Checkout session for subscription.

    Args:
        user_id: Supabase user ID
        email: User's email address
        tier: Subscription tier (pro, enterprise)
        interval: Billing interval (monthly, yearly)

    Returns:
        Checkout session URL

    Raises:
        HTTPException if Stripe not configured or checkout fails
    """
    if not is_stripe_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Zahlungssystem nicht konfiguriert"
        )

    price_id = get_price_id(tier, interval)
    if not price_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ungültiger Tarif oder Intervall: {tier}/{interval}"
        )

    try:
        # Create or retrieve customer
        customers = stripe.Customer.list(email=email, limit=1)
        if customers.data:
            customer = customers.data[0]
        else:
            customer = stripe.Customer.create(
                email=email,
                metadata={"user_id": user_id}
            )

        # Create checkout session
        session = stripe.checkout.Session.create(
            customer=customer.id,
            payment_method_types=["card"],
            line_items=[{
                "price": price_id,
                "quantity": 1
            }],
            mode="subscription",
            success_url=SUCCESS_URL,
            cancel_url=CANCEL_URL,
            metadata={
                "user_id": user_id,
                "tier": tier
            },
            subscription_data={
                "metadata": {
                    "user_id": user_id,
                    "tier": tier
                }
            }
        )

        return session.url

    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Zahlungsfehler: {str(e)}"
        )


async def create_portal_session(user_id: str, email: str) -> str:
    """
    Create a Stripe Customer Portal session for subscription management.

    Args:
        user_id: Supabase user ID
        email: User's email address

    Returns:
        Portal session URL

    Raises:
        HTTPException if no customer found or portal creation fails
    """
    if not is_stripe_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Zahlungssystem nicht konfiguriert"
        )

    try:
        # Find customer
        customers = stripe.Customer.list(email=email, limit=1)
        if not customers.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Kein Abonnement gefunden"
            )

        customer = customers.data[0]

        # Create portal session
        session = stripe.billing_portal.Session.create(
            customer=customer.id,
            return_url=FRONTEND_URL
        )

        return session.url

    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Portal-Fehler: {str(e)}"
        )


# ============================================================================
# Webhook Handling
# ============================================================================

async def handle_webhook(request: Request) -> dict:
    """
    Handle Stripe webhook events.

    Processes subscription lifecycle events to update user tiers.

    Args:
        request: FastAPI request object

    Returns:
        Status dict

    Raises:
        HTTPException if webhook verification fails
    """
    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Webhook nicht konfiguriert"
        )

    # Get raw body and signature
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not sig_header:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fehlender Signatur-Header"
        )

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ungültige Nutzlast"
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ungültige Signatur"
        )

    # Handle events
    event_type = event["type"]
    data = event["data"]["object"]

    if event_type == "checkout.session.completed":
        # Checkout completed - subscription started
        await handle_checkout_completed(data)

    elif event_type == "customer.subscription.updated":
        # Subscription updated (e.g., plan change)
        await handle_subscription_updated(data)

    elif event_type == "customer.subscription.deleted":
        # Subscription cancelled
        await handle_subscription_deleted(data)

    elif event_type == "invoice.payment_failed":
        # Payment failed - notify user
        await handle_payment_failed(data)

    return {"status": "ok", "event": event_type}


async def handle_checkout_completed(session: dict):
    """Handle successful checkout completion."""
    user_id = session.get("metadata", {}).get("user_id")
    tier = session.get("metadata", {}).get("tier", UserTier.PRO)

    if user_id:
        await update_user_tier(user_id, tier)
        print(f"User {user_id} upgraded to {tier} via checkout")


async def handle_subscription_updated(subscription: dict):
    """Handle subscription updates (plan changes, renewals)."""
    user_id = subscription.get("metadata", {}).get("user_id")

    if not user_id:
        return

    # Get current status and plan
    status = subscription.get("status")

    if status == "active":
        # Determine tier from price
        items = subscription.get("items", {}).get("data", [])
        if items:
            price_id = items[0].get("price", {}).get("id")
            tier = tier_from_price_id(price_id)
            await update_user_tier(user_id, tier)
            print(f"User {user_id} subscription updated to {tier}")

    elif status in ["past_due", "unpaid"]:
        # Payment issues - could notify user
        print(f"User {user_id} subscription payment issue: {status}")


async def handle_subscription_deleted(subscription: dict):
    """Handle subscription cancellation."""
    user_id = subscription.get("metadata", {}).get("user_id")

    if user_id:
        # Downgrade to free tier
        await update_user_tier(user_id, UserTier.FREE)
        print(f"User {user_id} downgraded to free (subscription cancelled)")


async def handle_payment_failed(invoice: dict):
    """Handle failed payment."""
    customer_id = invoice.get("customer")

    if customer_id:
        try:
            customer = stripe.Customer.retrieve(customer_id)
            user_id = customer.get("metadata", {}).get("user_id")
            if user_id:
                print(f"Payment failed for user {user_id}")
                # Could send notification email here
        except Exception as e:
            print(f"Error handling payment failure: {e}")


# ============================================================================
# Subscription Status
# ============================================================================

async def get_subscription_status(email: str) -> dict:
    """
    Get current subscription status for a user.

    Args:
        email: User's email address

    Returns:
        Subscription status dict
    """
    if not is_stripe_configured():
        return {"status": "not_configured"}

    try:
        customers = stripe.Customer.list(email=email, limit=1)
        if not customers.data:
            return {"status": "no_customer"}

        customer = customers.data[0]

        # Get active subscriptions
        subscriptions = stripe.Subscription.list(
            customer=customer.id,
            status="active",
            limit=1
        )

        if not subscriptions.data:
            return {
                "status": "no_subscription",
                "customer_id": customer.id
            }

        sub = subscriptions.data[0]
        items = sub.get("items", {}).get("data", [])
        price_id = items[0].get("price", {}).get("id") if items else None

        return {
            "status": "active",
            "subscription_id": sub.id,
            "customer_id": customer.id,
            "tier": tier_from_price_id(price_id) if price_id else "unknown",
            "current_period_end": sub.get("current_period_end"),
            "cancel_at_period_end": sub.get("cancel_at_period_end", False)
        }

    except stripe.error.StripeError as e:
        return {"status": "error", "message": str(e)}

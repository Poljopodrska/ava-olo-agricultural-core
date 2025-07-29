#!/usr/bin/env python3
"""
Stripe Webhook Handler for AVA OLO
Processes Stripe events for subscription lifecycle
"""
import os
import logging
import stripe
from datetime import datetime
from fastapi import APIRouter, Request, HTTPException, Header
from typing import Optional
import asyncpg

from modules.stripe_integration import update_subscription_status

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')
DATABASE_URL = os.getenv('DATABASE_URL')


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None)
):
    """Handle Stripe webhook events"""
    payload = await request.body()
    
    # Verify webhook signature
    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        logger.error(f"Invalid payload: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Handle the event
    logger.info(f"Received Stripe event: {event['type']}")
    
    try:
        if event['type'] == 'checkout.session.completed':
            await handle_checkout_completed(event['data']['object'])
        
        elif event['type'] == 'customer.subscription.created':
            await handle_subscription_created(event['data']['object'])
        
        elif event['type'] == 'customer.subscription.updated':
            await handle_subscription_updated(event['data']['object'])
        
        elif event['type'] == 'customer.subscription.deleted':
            await handle_subscription_deleted(event['data']['object'])
        
        elif event['type'] == 'invoice.payment_succeeded':
            await handle_payment_succeeded(event['data']['object'])
        
        elif event['type'] == 'invoice.payment_failed':
            await handle_payment_failed(event['data']['object'])
        
        else:
            logger.info(f"Unhandled event type: {event['type']}")
    
    except Exception as e:
        logger.error(f"Error handling webhook: {str(e)}")
        # Return 200 to acknowledge receipt, even if processing failed
        # Stripe will retry if we return an error
    
    return {"status": "success"}


async def handle_checkout_completed(session):
    """Handle successful checkout completion"""
    farmer_id = session['metadata'].get('farmer_id')
    if not farmer_id:
        logger.error("No farmer_id in checkout session metadata")
        return
    
    # Get subscription ID from session
    subscription_id = session['subscription']
    
    # Retrieve subscription details
    subscription = stripe.Subscription.retrieve(subscription_id)
    
    # Update farmer record
    await update_subscription_status(
        farmer_id=int(farmer_id),
        status='active',
        subscription_id=subscription_id,
        current_period_end=datetime.fromtimestamp(subscription['current_period_end'])
    )
    
    logger.info(f"Checkout completed for farmer {farmer_id}, subscription {subscription_id}")


async def handle_subscription_created(subscription):
    """Handle new subscription creation"""
    # Get farmer ID from customer metadata
    customer = stripe.Customer.retrieve(subscription['customer'])
    farmer_id = customer['metadata'].get('farmer_id')
    
    if not farmer_id:
        logger.error(f"No farmer_id in customer metadata for {subscription['customer']}")
        return
    
    # Update subscription details
    await update_subscription_status(
        farmer_id=int(farmer_id),
        status='active' if subscription['status'] == 'active' else 'trial',
        subscription_id=subscription['id'],
        current_period_end=datetime.fromtimestamp(subscription['current_period_end'])
    )
    
    # Record payment if not in trial
    if subscription['status'] == 'active':
        await record_payment(
            farmer_id=int(farmer_id),
            amount_cents=subscription['items']['data'][0]['price']['unit_amount'],
            status='succeeded',
            description='Subscription payment'
        )


async def handle_subscription_updated(subscription):
    """Handle subscription updates (renewals, plan changes, etc)"""
    customer = stripe.Customer.retrieve(subscription['customer'])
    farmer_id = customer['metadata'].get('farmer_id')
    
    if not farmer_id:
        return
    
    # Map Stripe status to our status
    status_map = {
        'active': 'active',
        'past_due': 'past_due',
        'canceled': 'canceled',
        'unpaid': 'unpaid',
        'trialing': 'trial'
    }
    
    our_status = status_map.get(subscription['status'], 'inactive')
    
    await update_subscription_status(
        farmer_id=int(farmer_id),
        status=our_status,
        current_period_end=datetime.fromtimestamp(subscription['current_period_end'])
    )
    
    # If subscription renewed, reset usage counters
    if subscription['status'] == 'active' and 'previous_attributes' in subscription:
        if 'current_period_end' in subscription['previous_attributes']:
            await reset_usage_counters(int(farmer_id))


async def handle_subscription_deleted(subscription):
    """Handle subscription cancellation"""
    customer = stripe.Customer.retrieve(subscription['customer'])
    farmer_id = customer['metadata'].get('farmer_id')
    
    if not farmer_id:
        return
    
    await update_subscription_status(
        farmer_id=int(farmer_id),
        status='canceled'
    )
    
    logger.info(f"Subscription canceled for farmer {farmer_id}")


async def handle_payment_succeeded(invoice):
    """Handle successful payment"""
    customer_id = invoice['customer']
    customer = stripe.Customer.retrieve(customer_id)
    farmer_id = customer['metadata'].get('farmer_id')
    
    if not farmer_id:
        return
    
    # Record successful payment
    await record_payment(
        farmer_id=int(farmer_id),
        amount_cents=invoice['amount_paid'],
        stripe_payment_intent_id=invoice['payment_intent'],
        status='succeeded',
        description=f"Invoice {invoice['number']}"
    )


async def handle_payment_failed(invoice):
    """Handle failed payment"""
    customer_id = invoice['customer']
    customer = stripe.Customer.retrieve(customer_id)
    farmer_id = customer['metadata'].get('farmer_id')
    
    if not farmer_id:
        return
    
    # Record failed payment
    await record_payment(
        farmer_id=int(farmer_id),
        amount_cents=invoice['amount_due'],
        stripe_payment_intent_id=invoice['payment_intent'],
        status='failed',
        description=f"Failed payment for invoice {invoice['number']}"
    )
    
    # Update subscription status
    await update_subscription_status(
        farmer_id=int(farmer_id),
        status='past_due'
    )


async def record_payment(
    farmer_id: int,
    amount_cents: int,
    status: str,
    description: str,
    stripe_payment_intent_id: Optional[str] = None
):
    """Record payment in database"""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute("""
            INSERT INTO payment_history 
            (farmer_id, stripe_payment_intent_id, amount_cents, status, description)
            VALUES ($1, $2, $3, $4, $5)
        """, farmer_id, stripe_payment_intent_id, amount_cents, status, description)
    finally:
        await conn.close()


async def reset_usage_counters(farmer_id: int):
    """Reset usage counters for new billing period"""
    # Usage is tracked with billing period dates, so no action needed
    # The usage queries automatically filter by current period
    logger.info(f"New billing period started for farmer {farmer_id}")


@router.get("/stripe/config")
async def get_stripe_config():
    """Get Stripe publishable key for frontend"""
    return {
        "publishable_key": os.getenv('STRIPE_PUBLISHABLE_KEY'),
        "webhook_configured": bool(STRIPE_WEBHOOK_SECRET)
    }
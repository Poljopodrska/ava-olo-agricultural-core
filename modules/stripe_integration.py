#!/usr/bin/env python3
"""
Stripe Payment Integration for AVA OLO
Handles subscriptions, checkout sessions, and payment management
"""
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import stripe
from fastapi import HTTPException
import asyncpg

logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL')


async def get_config_value(key: str) -> str:
    """Get configuration value from database"""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        value = await conn.fetchval(
            "SELECT config_value FROM subscription_config WHERE config_key = $1",
            key
        )
        return value
    finally:
        await conn.close()


async def update_config_value(key: str, value: str, updated_by: str):
    """Update configuration value with audit trail"""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # Get old value for audit
        old_value = await conn.fetchval(
            "SELECT config_value FROM subscription_config WHERE config_key = $1",
            key
        )
        
        # Update config
        await conn.execute("""
            UPDATE subscription_config 
            SET config_value = $1, updated_at = NOW(), updated_by = $2
            WHERE config_key = $3
        """, value, updated_by, key)
        
        # Log to audit table
        await conn.execute("""
            INSERT INTO config_audit_log (config_key, old_value, new_value, changed_by)
            VALUES ($1, $2, $3, $4)
        """, key, old_value, value, updated_by)
        
    finally:
        await conn.close()


async def get_farmer(farmer_id: int) -> Optional[Dict]:
    """Get farmer details by ID"""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        farmer = await conn.fetchrow("""
            SELECT * FROM farmers WHERE id = $1
        """, farmer_id)
        return dict(farmer) if farmer else None
    finally:
        await conn.close()


async def update_farmer_stripe_id(farmer_id: int, stripe_customer_id: str):
    """Update farmer's Stripe customer ID"""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute("""
            UPDATE farmers 
            SET stripe_customer_id = $1
            WHERE id = $2
        """, stripe_customer_id, farmer_id)
    finally:
        await conn.close()


async def create_checkout_session(farmer_id: int, return_url: str) -> str:
    """Create Stripe Checkout session for subscription"""
    farmer = await get_farmer(farmer_id)
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")
    
    # Get configured price
    price_cents = int(await get_config_value('monthly_price_cents'))
    api_limit = await get_config_value('api_call_limit')
    whatsapp_limit = await get_config_value('whatsapp_message_limit')
    
    # Create or retrieve Stripe customer
    if not farmer.get('stripe_customer_id'):
        customer = stripe.Customer.create(
            email=farmer.get('email'),
            phone=farmer.get('phone'),
            name=f"{farmer.get('manager_name')} {farmer.get('manager_last_name', '')}".strip(),
            metadata={'farmer_id': str(farmer_id)}
        )
        await update_farmer_stripe_id(farmer_id, customer.id)
        stripe_customer_id = customer.id
    else:
        stripe_customer_id = farmer['stripe_customer_id']
    
    # Create checkout session
    try:
        session = stripe.checkout.Session.create(
            customer=stripe_customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'eur',
                    'product_data': {
                        'name': 'AVA OLO Farm Subscription',
                        'description': f'Monthly subscription: {api_limit} API calls, {whatsapp_limit} WhatsApp messages',
                        'images': ['https://ava-olo.com/images/logo.png']
                    },
                    'unit_amount': price_cents,
                    'recurring': {
                        'interval': 'month',
                        'interval_count': 1
                    }
                },
                'quantity': 1
            }],
            mode='subscription',
            success_url=f"{return_url}?success=true&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{return_url}?canceled=true",
            metadata={
                'farmer_id': str(farmer_id)
            },
            subscription_data={
                'trial_period_days': int(await get_config_value('trial_days'))
            }
        )
        
        logger.info(f"Created checkout session {session.id} for farmer {farmer_id}")
        return session.url
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating checkout session: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


async def get_farmer_by_phone(phone: str) -> Optional[Dict]:
    """Get farmer by WhatsApp phone number"""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # Clean phone number (remove whatsapp: prefix if present)
        clean_phone = phone.replace('whatsapp:', '')
        
        farmer = await conn.fetchrow("""
            SELECT * FROM farmers 
            WHERE wa_phone_number = $1 OR phone = $1
            LIMIT 1
        """, clean_phone)
        return dict(farmer) if farmer else None
    finally:
        await conn.close()


async def has_active_subscription(farmer_id: int) -> bool:
    """Check if farmer has active subscription (including trial)"""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        farmer = await conn.fetchrow("""
            SELECT subscription_status, trial_end_date, current_period_end
            FROM farmers WHERE id = $1
        """, farmer_id)
        
        if not farmer:
            return False
        
        status = farmer['subscription_status']
        now = datetime.utcnow()
        
        # Check trial
        if status == 'trial' and farmer['trial_end_date']:
            return farmer['trial_end_date'] > now
        
        # Check active subscription
        if status == 'active' and farmer['current_period_end']:
            return farmer['current_period_end'] > now
        
        return False
        
    finally:
        await conn.close()


async def get_current_period_usage(farmer_id: int, tracking_type: str) -> int:
    """Get usage count for current billing period"""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # Get farmer's billing period
        farmer = await conn.fetchrow("""
            SELECT subscription_status, trial_end_date, current_period_end
            FROM farmers WHERE id = $1
        """, farmer_id)
        
        if not farmer:
            return 0
        
        # Determine billing period
        now = datetime.utcnow()
        if farmer['subscription_status'] == 'trial':
            # For trial, count from account creation to trial end
            period_start = farmer['trial_end_date'] - timedelta(days=7)
            period_end = farmer['trial_end_date']
        else:
            # For active subscription, use current period
            if farmer['current_period_end']:
                period_end = farmer['current_period_end']
                period_start = period_end - timedelta(days=30)
            else:
                return 0
        
        # Count usage in period
        count = await conn.fetchval("""
            SELECT COUNT(*) FROM usage_tracking
            WHERE farmer_id = $1 
            AND tracking_type = $2
            AND timestamp BETWEEN $3 AND $4
        """, farmer_id, tracking_type, period_start, period_end)
        
        return count or 0
        
    finally:
        await conn.close()


async def record_usage(farmer_id: int, tracking_type: str, endpoint: str):
    """Record API or WhatsApp usage"""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # Get farmer's billing period
        farmer = await conn.fetchrow("""
            SELECT subscription_status, trial_end_date, current_period_end
            FROM farmers WHERE id = $1
        """, farmer_id)
        
        # Determine billing period
        now = datetime.utcnow()
        if farmer['subscription_status'] == 'trial':
            period_start = farmer['trial_end_date'] - timedelta(days=7)
            period_end = farmer['trial_end_date']
        else:
            if farmer['current_period_end']:
                period_end = farmer['current_period_end']
                period_start = period_end - timedelta(days=30)
            else:
                # No active period, use current month
                period_start = now.replace(day=1, hour=0, minute=0, second=0)
                period_end = (period_start + timedelta(days=32)).replace(day=1)
        
        # Record usage
        await conn.execute("""
            INSERT INTO usage_tracking 
            (farmer_id, tracking_type, endpoint, billing_period_start, billing_period_end)
            VALUES ($1, $2, $3, $4, $5)
        """, farmer_id, tracking_type, endpoint, period_start, period_end)
        
    finally:
        await conn.close()


async def update_subscription_status(
    farmer_id: int, 
    status: str, 
    subscription_id: Optional[str] = None,
    current_period_end: Optional[datetime] = None
):
    """Update farmer's subscription status"""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        query_parts = ["UPDATE farmers SET subscription_status = $1"]
        params = [status]
        param_count = 1
        
        if subscription_id is not None:
            param_count += 1
            query_parts.append(f", subscription_id = ${param_count}")
            params.append(subscription_id)
        
        if current_period_end is not None:
            param_count += 1
            query_parts.append(f", current_period_end = ${param_count}")
            params.append(current_period_end)
        
        param_count += 1
        query_parts.append(f" WHERE id = ${param_count}")
        params.append(farmer_id)
        
        query = "".join(query_parts)
        await conn.execute(query, *params)
        
        logger.info(f"Updated subscription status for farmer {farmer_id}: {status}")
        
    finally:
        await conn.close()


async def create_payment_link_message(farmer_id: int) -> str:
    """Create WhatsApp message with payment link"""
    farmer = await get_farmer(farmer_id)
    if not farmer:
        raise ValueError("Farmer not found")
    
    # Create checkout session
    base_url = os.getenv('BASE_URL', 'https://ava-olo.com')
    checkout_url = await create_checkout_session(
        farmer_id, 
        f"{base_url}/payment-complete"
    )
    
    # Get pricing info
    price = float(await get_config_value('monthly_price_cents')) / 100
    api_limit = await get_config_value('api_call_limit')
    whatsapp_limit = await get_config_value('whatsapp_message_limit')
    
    # Create message
    message = f"""🌱 Your AVA OLO trial is ending soon!

Continue getting expert agricultural advice for just €{price:.2f}/month

👉 Subscribe here: {checkout_url}

Your subscription includes:
✅ {api_limit} API calls per month
✅ {whatsapp_limit} WhatsApp messages
✅ Real-time weather updates
✅ Personalized crop advice
✅ Disease and pest alerts
✅ Market price information

Need help? Reply with your questions!"""
    
    return message


async def get_subscription_metrics() -> Dict:
    """Get subscription metrics for admin dashboard"""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # Total farmers
        total_farmers = await conn.fetchval("SELECT COUNT(*) FROM farmers")
        
        # Subscription status breakdown
        status_counts = await conn.fetch("""
            SELECT subscription_status, COUNT(*) as count
            FROM farmers
            GROUP BY subscription_status
        """)
        
        # Revenue metrics
        active_subs = await conn.fetchval("""
            SELECT COUNT(*) FROM farmers 
            WHERE subscription_status = 'active'
        """)
        
        monthly_price = float(await get_config_value('monthly_price_cents')) / 100
        monthly_revenue = active_subs * monthly_price
        
        # Usage metrics
        current_month_usage = await conn.fetch("""
            SELECT tracking_type, COUNT(*) as count
            FROM usage_tracking
            WHERE timestamp >= date_trunc('month', NOW())
            GROUP BY tracking_type
        """)
        
        return {
            'total_farmers': total_farmers,
            'subscription_breakdown': {row['subscription_status']: row['count'] for row in status_counts},
            'monthly_revenue_eur': monthly_revenue,
            'active_subscriptions': active_subs,
            'current_month_usage': {row['tracking_type']: row['count'] for row in current_month_usage},
            'current_pricing': {
                'monthly_price_eur': monthly_price,
                'api_limit': int(await get_config_value('api_call_limit')),
                'whatsapp_limit': int(await get_config_value('whatsapp_message_limit'))
            }
        }
        
    finally:
        await conn.close()
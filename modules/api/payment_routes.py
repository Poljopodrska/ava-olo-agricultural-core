#!/usr/bin/env python3
"""
Payment API Routes for AVA OLO
Handles subscription management and payment processing
"""
from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import RedirectResponse
from typing import Optional
import logging

from modules.stripe_integration import (
    create_checkout_session,
    get_farmer,
    has_active_subscription,
    get_current_period_usage,
    get_config_value,
    create_payment_link_message,
    get_farmer_by_phone
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/payment", tags=["payment"])


@router.get("/subscribe")
async def create_subscription(
    farmer_id: int = Query(..., description="Farmer ID"),
    return_url: Optional[str] = Query(None, description="URL to return after payment")
):
    """Create Stripe checkout session for subscription"""
    # Verify farmer exists
    farmer = await get_farmer(farmer_id)
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")
    
    # Check if already has active subscription
    if await has_active_subscription(farmer_id):
        return {
            "status": "already_subscribed",
            "message": "Farmer already has an active subscription"
        }
    
    # Use default return URL if not provided
    if not return_url:
        import os
        base_url = os.getenv('BASE_URL', 'http://localhost:8000')
        return_url = f"{base_url}/subscription-success"
    
    try:
        # Create checkout session
        checkout_url = await create_checkout_session(farmer_id, return_url)
        
        # Return redirect to Stripe checkout
        return RedirectResponse(url=checkout_url, status_code=303)
        
    except Exception as e:
        logger.error(f"Error creating checkout session: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating payment session")


@router.post("/subscribe")
async def create_subscription_api(request: Request):
    """API endpoint to create subscription (returns JSON)"""
    data = await request.json()
    farmer_id = data.get('farmer_id')
    return_url = data.get('return_url')
    
    if not farmer_id:
        raise HTTPException(status_code=400, detail="farmer_id required")
    
    # Verify farmer exists
    farmer = await get_farmer(farmer_id)
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")
    
    # Check if already has active subscription
    if await has_active_subscription(farmer_id):
        return {
            "status": "already_subscribed",
            "message": "Farmer already has an active subscription"
        }
    
    # Use default return URL if not provided
    if not return_url:
        import os
        base_url = os.getenv('BASE_URL', 'http://localhost:8000')
        return_url = f"{base_url}/subscription-success"
    
    try:
        # Create checkout session
        checkout_url = await create_checkout_session(farmer_id, return_url)
        
        return {
            "status": "success",
            "checkout_url": checkout_url,
            "message": "Redirect user to checkout_url to complete payment"
        }
        
    except Exception as e:
        logger.error(f"Error creating checkout session: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating payment session")


@router.get("/status/{farmer_id}")
async def get_subscription_status(farmer_id: int):
    """Get farmer's subscription status and usage"""
    farmer = await get_farmer(farmer_id)
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")
    
    # Get subscription status
    has_subscription = await has_active_subscription(farmer_id)
    
    # Get usage data
    api_usage = await get_current_period_usage(farmer_id, 'api_call')
    whatsapp_usage = await get_current_period_usage(farmer_id, 'whatsapp_message')
    
    # Get limits
    api_limit = int(await get_config_value('api_call_limit'))
    whatsapp_limit = int(await get_config_value('whatsapp_message_limit'))
    
    # Get pricing
    monthly_price = float(await get_config_value('monthly_price_cents')) / 100
    
    return {
        "farmer_id": farmer_id,
        "has_active_subscription": has_subscription,
        "subscription_status": farmer.get('subscription_status', 'none'),
        "trial_end_date": farmer.get('trial_end_date'),
        "current_period_end": farmer.get('current_period_end'),
        "usage": {
            "api_calls": {
                "used": api_usage,
                "limit": api_limit,
                "remaining": max(0, api_limit - api_usage)
            },
            "whatsapp_messages": {
                "used": whatsapp_usage,
                "limit": whatsapp_limit,
                "remaining": max(0, whatsapp_limit - whatsapp_usage)
            }
        },
        "pricing": {
            "monthly_price_eur": monthly_price,
            "currency": "EUR"
        }
    }


@router.post("/whatsapp-payment-link")
async def send_whatsapp_payment_link(request: Request):
    """Send payment link via WhatsApp"""
    data = await request.json()
    phone = data.get('phone')
    
    if not phone:
        raise HTTPException(status_code=400, detail="phone number required")
    
    # Find farmer by phone
    farmer = await get_farmer_by_phone(phone)
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found with this phone number")
    
    # Check if already subscribed
    if await has_active_subscription(farmer['id']):
        return {
            "status": "already_subscribed",
            "message": "Farmer already has an active subscription"
        }
    
    try:
        # Create payment link message
        message = await create_payment_link_message(farmer['id'])
        
        # TODO: Send via WhatsApp (integrate with WhatsApp module)
        # For now, return the message
        return {
            "status": "success",
            "farmer_id": farmer['id'],
            "message": message,
            "note": "WhatsApp sending will be integrated with WhatsApp module"
        }
        
    except Exception as e:
        logger.error(f"Error creating payment link: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating payment link")


@router.get("/pricing")
async def get_current_pricing():
    """Get current pricing configuration"""
    return {
        "monthly_price_eur": float(await get_config_value('monthly_price_cents')) / 100,
        "trial_days": int(await get_config_value('trial_days')),
        "limits": {
            "api_calls": int(await get_config_value('api_call_limit')),
            "whatsapp_messages": int(await get_config_value('whatsapp_message_limit'))
        },
        "overflow_pricing": {
            "api_call_eur": float(await get_config_value('overflow_api_price_cents')) / 100,
            "whatsapp_message_eur": float(await get_config_value('overflow_message_price_cents')) / 100
        },
        "currency": "EUR"
    }
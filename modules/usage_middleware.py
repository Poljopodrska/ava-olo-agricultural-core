#!/usr/bin/env python3
"""
Usage Tracking Middleware for AVA OLO
Tracks API calls and enforces subscription limits
"""
import logging
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from datetime import datetime
import asyncpg
import os
from typing import Optional

from modules.stripe_integration import (
    has_active_subscription,
    get_current_period_usage,
    record_usage,
    get_config_value,
    get_farmer
)

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv('DATABASE_URL')

# Endpoints that should be tracked
TRACKED_ENDPOINTS = [
    '/api/v1/chat',
    '/api/v1/weather',
    '/api/v1/fields',
    '/api/v1/advice',
    '/api/v1/market-prices',
    '/api/v1/disease-detection',
    '/api/v1/irrigation',
    '/api/v1/harvest-prediction'
]

# Endpoints that should not be tracked
EXEMPT_ENDPOINTS = [
    '/api/v1/payment',
    '/api/v1/subscription',
    '/api/v1/auth',
    '/api/health',
    '/api/v1/admin',
    '/webhooks',
    '/static',
    '/docs',
    '/openapi.json'
]


def should_track_endpoint(path: str) -> bool:
    """Check if endpoint should be tracked for usage"""
    # Don't track exempt endpoints
    for exempt in EXEMPT_ENDPOINTS:
        if path.startswith(exempt):
            return False
    
    # Track specific endpoints
    for tracked in TRACKED_ENDPOINTS:
        if path.startswith(tracked):
            return True
    
    # Track all WhatsApp endpoints
    if '/whatsapp' in path and '/webhook' in path:
        return True
    
    return False


async def get_farmer_from_request(request: Request) -> Optional[dict]:
    """Extract farmer information from request"""
    # Try to get farmer from different sources
    
    # 1. Check authorization header
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        # TODO: Implement token validation and farmer lookup
        # For now, we'll skip this
        pass
    
    # 2. Check session
    session_id = request.cookies.get('session_id')
    if session_id:
        # TODO: Implement session lookup
        pass
    
    # 3. Check query parameters
    farmer_id = request.query_params.get('farmer_id')
    if farmer_id:
        try:
            return await get_farmer(int(farmer_id))
        except:
            pass
    
    # 4. For WhatsApp, extract from form data
    if '/whatsapp' in str(request.url):
        try:
            form_data = await request.form()
            phone = form_data.get('From', '').replace('whatsapp:', '')
            if phone:
                conn = await asyncpg.connect(DATABASE_URL)
                try:
                    farmer = await conn.fetchrow("""
                        SELECT * FROM farmers 
                        WHERE wa_phone_number = $1 OR phone = $1
                        LIMIT 1
                    """, phone)
                    return dict(farmer) if farmer else None
                finally:
                    await conn.close()
        except:
            pass
    
    return None


async def track_usage_middleware(request: Request, call_next):
    """Middleware to track API usage and enforce limits"""
    
    # Check if we should track this endpoint
    if not should_track_endpoint(str(request.url.path)):
        return await call_next(request)
    
    # Try to identify the farmer
    farmer = await get_farmer_from_request(request)
    
    if farmer:
        farmer_id = farmer['id']
        
        # Handle linked accounts - use primary account for billing
        if farmer.get('linked_to_farmer_id'):
            primary_id = farmer['linked_to_farmer_id']
        else:
            primary_id = farmer_id
        
        # Check subscription status
        if not await has_active_subscription(primary_id):
            # Check if in trial that expired
            trial_end = farmer.get('trial_end_date')
            if trial_end and trial_end < datetime.utcnow():
                message = "Your 7-day trial has expired. Please subscribe to continue using AVA OLO."
            else:
                message = "Please subscribe to continue using AVA OLO"
            
            return JSONResponse(
                status_code=402,  # Payment Required
                content={
                    "error": "subscription_required",
                    "message": message,
                    "payment_url": f"/api/v1/payment/subscribe?farmer_id={primary_id}",
                    "trial_expired": trial_end < datetime.utcnow() if trial_end else False
                }
            )
        
        # Determine tracking type
        if '/whatsapp' in str(request.url.path):
            tracking_type = 'whatsapp_message'
            limit_key = 'whatsapp_message_limit'
        else:
            tracking_type = 'api_call'
            limit_key = 'api_call_limit'
        
        # Check usage limits
        limit = int(await get_config_value(limit_key))
        current_usage = await get_current_period_usage(primary_id, tracking_type)
        
        if current_usage >= limit:
            # Get overflow pricing
            if tracking_type == 'api_call':
                overflow_price = float(await get_config_value('overflow_api_price_cents')) / 100
                overflow_unit = "API call"
            else:
                overflow_price = float(await get_config_value('overflow_message_price_cents')) / 100
                overflow_unit = "WhatsApp message"
            
            return JSONResponse(
                status_code=429,  # Too Many Requests
                content={
                    "error": "usage_limit_exceeded",
                    "message": f"Monthly {tracking_type.replace('_', ' ')} limit reached",
                    "limit": limit,
                    "usage": current_usage,
                    "period_end": farmer.get('current_period_end').isoformat() if farmer.get('current_period_end') else None,
                    "overflow_pricing": {
                        "price_eur": overflow_price,
                        "unit": overflow_unit,
                        "message": f"Additional {overflow_unit}s are €{overflow_price:.2f} each"
                    }
                }
            )
        
        # Record the usage
        try:
            await record_usage(primary_id, tracking_type, str(request.url.path))
        except Exception as e:
            logger.error(f"Error recording usage: {str(e)}")
            # Don't block the request if usage recording fails
    
    # Continue with the request
    response = await call_next(request)
    
    # Add usage headers to response if farmer identified
    if farmer:
        try:
            current_usage = await get_current_period_usage(primary_id, tracking_type)
            limit = int(await get_config_value(limit_key))
            response.headers["X-Usage-Limit"] = str(limit)
            response.headers["X-Usage-Current"] = str(current_usage)
            response.headers["X-Usage-Remaining"] = str(max(0, limit - current_usage))
        except:
            pass
    
    return response
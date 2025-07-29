#!/usr/bin/env python3
"""
Admin Routes for AVA OLO
Handles pricing configuration and subscription management
"""
from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Optional
import logging

from modules.stripe_integration import (
    get_config_value,
    update_config_value,
    get_subscription_metrics
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


class PricingConfig(BaseModel):
    monthly_price: float  # in EUR
    trial_days: int
    api_call_limit: int
    whatsapp_limit: int
    overflow_api_price: Optional[float] = 0.01  # EUR per call
    overflow_message_price: Optional[float] = 0.02  # EUR per message


# Simple auth check - in production, use proper authentication
async def verify_admin(request: Request):
    """Verify admin access - placeholder for real auth"""
    # TODO: Implement proper admin authentication
    admin_token = request.headers.get('X-Admin-Token')
    if admin_token != "admin-secret-token":  # Replace with real auth
        raise HTTPException(status_code=403, detail="Admin access required")
    return True


@router.get("/pricing-config", dependencies=[Depends(verify_admin)])
async def get_pricing_config():
    """Get current pricing and limits configuration"""
    try:
        return {
            "monthly_price": float(await get_config_value('monthly_price_cents')) / 100,
            "trial_days": int(await get_config_value('trial_days')),
            "api_call_limit": int(await get_config_value('api_call_limit')),
            "whatsapp_limit": int(await get_config_value('whatsapp_message_limit')),
            "overflow_api_price": float(await get_config_value('overflow_api_price_cents')) / 100,
            "overflow_message_price": float(await get_config_value('overflow_message_price_cents')) / 100
        }
    except Exception as e:
        logger.error(f"Error getting pricing config: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving configuration")


@router.post("/pricing-config", dependencies=[Depends(verify_admin)])
async def update_pricing_config(config: PricingConfig, request: Request):
    """Update pricing and limits configuration"""
    # Get admin user identifier (from auth in production)
    admin_user = request.headers.get('X-Admin-User', 'admin')
    
    try:
        # Update all configuration values
        updates = [
            ('monthly_price_cents', str(int(config.monthly_price * 100))),
            ('trial_days', str(config.trial_days)),
            ('api_call_limit', str(config.api_call_limit)),
            ('whatsapp_message_limit', str(config.whatsapp_limit)),
            ('overflow_api_price_cents', str(int(config.overflow_api_price * 100))),
            ('overflow_message_price_cents', str(int(config.overflow_message_price * 100)))
        ]
        
        for key, value in updates:
            await update_config_value(key, value, admin_user)
        
        logger.info(f"Pricing configuration updated by {admin_user}")
        
        # Note: Existing subscriptions keep their current price
        # Only new subscriptions will use the updated pricing
        
        return {
            "status": "success",
            "message": "Configuration updated successfully",
            "updated_by": admin_user,
            "note": "Existing subscriptions maintain their current pricing"
        }
        
    except Exception as e:
        logger.error(f"Error updating pricing config: {str(e)}")
        raise HTTPException(status_code=500, detail="Error updating configuration")


@router.get("/subscription-metrics", dependencies=[Depends(verify_admin)])
async def get_metrics():
    """Get subscription and usage metrics"""
    try:
        metrics = await get_subscription_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Error getting metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving metrics")


@router.get("/config-history", dependencies=[Depends(verify_admin)])
async def get_config_history(limit: int = 50):
    """Get configuration change history"""
    import asyncpg
    import os
    
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        try:
            history = await conn.fetch("""
                SELECT * FROM config_audit_log
                ORDER BY changed_at DESC
                LIMIT $1
            """, limit)
            
            return [dict(row) for row in history]
            
        finally:
            await conn.close()
            
    except Exception as e:
        logger.error(f"Error getting config history: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving history")
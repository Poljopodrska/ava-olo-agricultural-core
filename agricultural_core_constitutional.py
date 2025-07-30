"""
AVA OLO Agricultural Core API with WhatsApp Integration
Version: 3.5.31
"""
import os
import logging
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Import configuration
from config import get_settings

# Import WhatsApp webhook handler
from modules.whatsapp.webhook_handler import router as whatsapp_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    logger.info("Starting AVA OLO Agricultural Core API v3.5.31")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"WhatsApp/Twilio enabled: {os.getenv('TWILIO_ENABLED', 'false')}")
    
    # Startup tasks
    yield
    
    # Shutdown tasks
    logger.info("Shutting down AVA OLO Agricultural Core API")

# Create FastAPI app
app = FastAPI(
    title="AVA OLO Agricultural Core API",
    description="Agricultural advisory system with WhatsApp integration",
    version="3.5.31",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(whatsapp_router)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "AVA OLO Agricultural Core",
        "version": "3.5.31",
        "status": "operational",
        "whatsapp_enabled": os.getenv("TWILIO_ENABLED", "false").lower() == "true"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "agricultural-core",
        "version": "3.5.31",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.ENVIRONMENT
    }

@app.get("/api/v1/health")
async def api_health_check():
    """API v1 health check"""
    whatsapp_status = "enabled" if os.getenv("TWILIO_ENABLED", "false").lower() == "true" else "disabled"
    
    return {
        "status": "healthy",
        "service": "agricultural-core-api",
        "version": "3.5.31",
        "timestamp": datetime.utcnow().isoformat(),
        "features": {
            "whatsapp": whatsapp_status,
            "database": "connected" if settings.DATABASE_URL else "not configured",
            "stripe": "enabled"  # Stripe package is now included
        }
    }

@app.get("/api/v1/payment/subscribe")
async def payment_subscribe(farmer_id: int):
    """Payment subscription endpoint with Stripe"""
    try:
        import stripe
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
        
        if not stripe.api_key:
            logger.error("Stripe API key not configured")
            raise HTTPException(status_code=500, detail="Payment system not configured")
        
        # Create Stripe checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'eur',
                    'product_data': {
                        'name': 'AVA OLO Agricultural Advisory Service',
                        'description': 'Monthly subscription for agricultural advice'
                    },
                    'unit_amount': 2000,  # €20.00
                    'recurring': {
                        'interval': 'month'
                    }
                },
                'quantity': 1,
            }],
            mode='subscription',
            success_url=f"{settings.BASE_URL}/payment/success?farmer_id={farmer_id}",
            cancel_url=f"{settings.BASE_URL}/payment/cancel",
            metadata={
                'farmer_id': str(farmer_id)
            }
        )
        
        # Return redirect to Stripe checkout
        return JSONResponse(
            content={"checkout_url": checkout_session.url},
            status_code=200,
            headers={"Location": checkout_session.url}
        )
        
    except Exception as e:
        logger.error(f"Payment error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": f"The requested resource {request.url.path} was not found",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    logger.error(f"Internal server error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.utcnow()
    
    # Log request
    logger.info(f"{request.method} {request.url.path}")
    
    # Process request
    response = await call_next(request)
    
    # Log response
    duration = (datetime.utcnow() - start_time).total_seconds()
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {duration:.3f}s")
    
    return response

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(
        "agricultural_core_constitutional:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )
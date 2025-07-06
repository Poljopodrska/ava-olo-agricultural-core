"""
AVA OLO Agronomic Service - Port 8003 
Redirects to new Agronomic Approval Dashboard on port 8007
"""
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import logging

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AVA OLO Agronomic Service Redirect",
    description="Redirects to new Agronomic Approval Dashboard",
    version="1.0.0"
)

# Setup templates
templates = Jinja2Templates(directory="services/templates")

@app.get("/", response_class=HTMLResponse)
async def redirect_to_new_dashboard(request: Request):
    """Redirect to new agronomic approval dashboard"""
    return templates.TemplateResponse("agronomic_redirect.html", {
        "request": request,
        "redirect_url": "http://localhost:8007",
        "redirect_delay": 3
    })

@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "service": "Agronomic Service Redirect",
        "status": "healthy",
        "port": 8003,
        "redirects_to": "http://localhost:8007",
        "purpose": "Redirects to new Agronomic Approval Dashboard"
    }

if __name__ == "__main__":
    import uvicorn
    print("🌾 Starting AVA OLO Agronomic Service Redirect on port 8003")
    uvicorn.run(app, host="0.0.0.0", port=8003)
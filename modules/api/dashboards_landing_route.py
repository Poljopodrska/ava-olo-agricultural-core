#!/usr/bin/env python3
"""
Dashboards Landing Page Route
Central hub for all AVA OLO dashboards
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import logging

from ..core.config import VERSION

logger = logging.getLogger(__name__)

router = APIRouter(tags=["dashboards"])
templates = Jinja2Templates(directory="templates")

@router.get("/dashboards", response_class=HTMLResponse)
async def dashboards_landing(request: Request):
    """
    Main dashboards landing page - provides links to all available dashboards
    including both local farmer dashboard and monitoring service dashboards
    """
    try:
        return templates.TemplateResponse("dashboards_landing.html", {
            "request": request,
            "version": VERSION
        })
    except Exception as e:
        logger.error(f"Error rendering dashboards landing page: {e}")
        # Return a simple HTML error page
        return HTMLResponse(
            content=f"""
            <html>
                <head><title>Error - AVA OLO Dashboards</title></head>
                <body>
                    <h1>Error Loading Dashboards</h1>
                    <p>Sorry, we couldn't load the dashboards page.</p>
                    <p>Error: {str(e)}</p>
                    <p><a href="/">Return to Home</a></p>
                </body>
            </html>
            """,
            status_code=500
        )
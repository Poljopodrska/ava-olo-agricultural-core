from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os

router = APIRouter(prefix="/farmer", tags=["farmer"])

# Templates directory
templates_dir = os.path.join(os.path.dirname(__file__), "..", "..", "templates")
if os.path.exists(templates_dir):
    templates = Jinja2Templates(directory=templates_dir)
else:
    templates = None

@router.get("/dashboard")
async def farmer_dashboard(request: Request, lang: str = "en"):
    """Farmer dashboard with language support"""
    
    # Language translations
    translations = {
        "en": {
            "dashboard_title": "Farmer Dashboard",
            "welcome": "Welcome",
            "weather": "Weather",
            "fields": "Fields",
            "tasks": "Tasks",
            "chat": "Chat Assistant"
        },
        "bg": {
            "dashboard_title": "Фермерско табло",
            "welcome": "Добре дошли",
            "weather": "Време",
            "fields": "Полета",
            "tasks": "Задачи",
            "chat": "Чат асистент"
        },
        "sl": {
            "dashboard_title": "Kmetijska nadzorna plošča",
            "welcome": "Dobrodošli",
            "weather": "Vreme",
            "fields": "Polja",
            "tasks": "Naloge",
            "chat": "Klepetalnik pomočnik"
        }
    }
    
    t = translations.get(lang, translations["en"])
    
    # If templates available, render HTML
    if templates:
        try:
            return templates.TemplateResponse("farmer/dashboard.html", {
                "request": request,
                "language": lang,
                "t": t,
                "farmer": {"name": "Test Farmer", "id": 1}
            })
        except:
            pass
    
    # Fallback to simple HTML
    html_content = f"""
    <html>
        <head>
            <title>{t['dashboard_title']}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #4CAF50; color: white; padding: 20px; }}
                .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{t['dashboard_title']}</h1>
                <p>{t['welcome']}, Test Farmer!</p>
            </div>
            <div class="section">
                <h2>{t['weather']}</h2>
                <p>Current: 22°C, Sunny</p>
            </div>
            <div class="section">
                <h2>{t['fields']}</h2>
                <p>Total fields: 2</p>
            </div>
            <div class="section">
                <h2>{t['tasks']}</h2>
                <p>Pending tasks: 3</p>
            </div>
            <div class="section">
                <h2>{t['chat']}</h2>
                <p>Chat assistant is available</p>
            </div>
        </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)
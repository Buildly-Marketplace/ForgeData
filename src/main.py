"""
ForgeData - Main FastAPI Application
Unified data exploration, ETL, reporting, and visualization platform
"""
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
import sys
from pathlib import Path

from src.routers import etl, reporting, explorer, auth, onboarding, analytics
from src.core.config import settings
from src.core.database import init_db

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="ForgeData",
    description="Universal Data Exploration, ETL, Reporting & Visualization Tool",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_path = Path(__file__).parent.parent / "static"
static_path.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Templates
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(etl.router, prefix="/api/etl", tags=["ETL"])
app.include_router(reporting.router, prefix="/api/reports", tags=["Reporting"])
app.include_router(explorer.router, prefix="/api/explore", tags=["Data Explorer"])
app.include_router(analytics.router)  # Analytics has its own prefix
app.include_router(onboarding.router)  # Onboarding has its own prefix

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("Starting ForgeData application...")
    await init_db()
    logger.info("ForgeData initialized successfully")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Main landing page"""
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "app_name": "ForgeData", "version": "1.0.0"}
    )

@app.get("/visualizations", response_class=HTMLResponse)
async def visualizations_page(request: Request):
    """Data visualization page with dual approaches"""
    return templates.TemplateResponse(
        "visualizations.html",
        {"request": request}
    )

@app.get("/etl", response_class=HTMLResponse)
async def etl_management_page(request: Request):
    """ETL pipeline management interface"""
    return templates.TemplateResponse(
        "etl.html",
        {"request": request}
    )

@app.get("/configuration", response_class=HTMLResponse)
async def configuration_page(request: Request):
    """Configuration and status management interface"""
    return templates.TemplateResponse(
        "configuration.html",
        {"request": request}
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse(
        content={
            "status": "healthy",
            "service": "ForgeData",
            "version": "1.0.0"
        }
    )

@app.get("/api/info")
async def api_info():
    """API information endpoint"""
    return {
        "name": "ForgeData",
        "version": "1.0.0",
        "description": "Universal Data Exploration, ETL, Reporting & Visualization Tool",
        "endpoints": {
            "auth": "/api/auth",
            "etl": "/api/etl",
            "reports": "/api/reports",
            "explore": "/api/explore"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )

import datetime
import logging
import os

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.database import get_db
from app.scraper import scrape_nike_sites
from config import get_config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

config = get_config()
app = FastAPI(title="Nike Missile Base Map")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.on_event("startup")
def startup() -> None:
    try:
        db_adapter = get_db()
        db_adapter.initialize()
        logger.info("Database initialized successfully")

        sites = db_adapter.get_all_sites()
        if not sites:
            logger.info("No Nike missile sites found in database. Loading data automatically...")
            sites_data = scrape_nike_sites()
            if sites_data:
                imported_count = db_adapter.import_sites(sites_data)
                logger.info("Successfully imported %s Nike missile sites on startup.", imported_count)
            else:
                logger.warning("No data found during automatic scraping.")
        else:
            logger.info("Found %s Nike missile sites in database.", len(sites))
    except Exception as exc:
        logger.error("Error initializing database: %s", exc)


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    google_maps_api_key = os.environ.get("GOOGLE_MAPS_API_KEY") or getattr(config, "GOOGLE_MAPS_API_KEY", "")

    if not google_maps_api_key:
        logger.warning("Google Maps API key not set. Map functionality will use Leaflet fallback.")

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "google_maps_api_key": google_maps_api_key,
            "now": datetime.datetime.now(),
        },
    )


@app.get("/about", response_class=HTMLResponse)
def about(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "about.html",
        {
            "request": request,
            "now": datetime.datetime.now(),
        },
    )


@app.get("/api/sites")
def get_sites(
    state: str | None = Query(default=None),
    site_type: str | None = Query(default=None),
) -> JSONResponse:
    try:
        db_adapter = get_db()
        sites = db_adapter.get_all_sites()

        if state:
            state_lower = state.lower()
            sites = [site for site in sites if site.get("state") and state_lower in site["state"].lower()]
        if site_type:
            sites = [site for site in sites if site.get("site_type") == site_type]

        return JSONResponse({"success": True, "count": len(sites), "sites": sites})
    except Exception as exc:
        logger.error("Error retrieving sites: %s", exc)
        return JSONResponse({"success": False, "error": str(exc)}, status_code=500)


@app.get("/api/sites/{site_id}")
def get_site(site_id: str) -> JSONResponse:
    try:
        db_adapter = get_db()
        site = db_adapter.get_site_by_id(site_id)

        if not site:
            raise HTTPException(status_code=404, detail="Site not found")

        return JSONResponse({"success": True, "site": site})
    except HTTPException as exc:
        return JSONResponse({"success": False, "error": exc.detail}, status_code=exc.status_code)
    except Exception as exc:
        logger.error("Error retrieving site %s: %s", site_id, exc)
        return JSONResponse({"success": False, "error": str(exc)}, status_code=500)


@app.post("/api/import-data")
def import_data() -> JSONResponse:
    try:
        db_adapter = get_db()
        db_adapter.initialize()

        sites_data = scrape_nike_sites()
        if not sites_data:
            return JSONResponse(
                {"success": False, "message": "No data found or error occurred during scraping."},
                status_code=500,
            )

        imported_count = db_adapter.import_sites(sites_data)
        return JSONResponse(
            {
                "success": True,
                "message": f"Successfully imported {imported_count} Nike missile sites.",
            }
        )
    except Exception as exc:
        logger.error("Error importing data: %s", exc)
        return JSONResponse({"success": False, "error": str(exc)}, status_code=500)


@app.post("/api/clear-data")
def clear_data() -> JSONResponse:
    try:
        db_adapter = get_db()
        sites = db_adapter.get_all_sites()

        for site in sites:
            db_adapter.delete_site(site["id"])

        return JSONResponse(
            {
                "success": True,
                "message": f"Successfully deleted {len(sites)} Nike missile sites.",
            }
        )
    except Exception as exc:
        logger.error("Error clearing data: %s", exc)
        return JSONResponse({"success": False, "error": str(exc)}, status_code=500)

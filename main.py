import datetime
import logging
import os
import secrets
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.concurrency import run_in_threadpool

from app.database import get_db
from app.scraper import scrape_nike_sites
from config import get_config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

config = get_config()
BASE_DIR = Path(__file__).resolve().parent


def require_admin(authorization: str | None = Header(default=None)) -> None:
    """Require a bearer token for operations that modify persisted site data."""
    expected_token = os.environ.get("ADMIN_API_TOKEN", "")
    if not expected_token:
        logger.error("ADMIN_API_TOKEN is not configured; rejecting administrative request")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Administrative operations are not configured",
        )

    scheme, separator, supplied_token = (authorization or "").partition(" ")
    if (
        not separator
        or scheme.lower() != "bearer"
        or not supplied_token
        or not secrets.compare_digest(supplied_token.encode("utf-8"), expected_token.encode("utf-8"))
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing administrative token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def startup() -> None:
    db_adapter = get_db()
    # Database failures must prevent startup, rather than serving a broken app.
    db_adapter.initialize()
    sites = db_adapter.get_all_sites()
    if sites or os.environ.get("AUTO_IMPORT_DATA", "true").lower() in {"0", "false", "no"}:
        logger.info("Found %s Nike site locations in database.", len(sites))
        return
    try:
        sites_data = scrape_nike_sites()
        if sites_data:
            imported_count = db_adapter.import_sites(sites_data)
            logger.info("Successfully imported %s site locations on startup.", imported_count)
        else:
            logger.warning("No data found during automatic scraping; use the import endpoint to retry.")
    except Exception:
        logger.exception("Automatic data import failed; use the import endpoint to retry")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await run_in_threadpool(startup)
    yield


app = FastAPI(title="Nike Missile Base Map", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=BASE_DIR / "app/static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "app/templates")


@app.get("/healthz")
def health() -> JSONResponse:
    try:
        get_db().get_all_sites()
        return JSONResponse({"status": "ok"})
    except Exception:
        logger.exception("Database health check failed")
        return JSONResponse({"status": "unavailable"}, status_code=503)


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    google_maps_api_key = os.environ.get("GOOGLE_MAPS_API_KEY") or getattr(config, "GOOGLE_MAPS_API_KEY", "")

    if not google_maps_api_key:
        logger.warning("Google Maps API key not set. Map functionality will use Leaflet fallback.")

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "request": request,
            "google_maps_api_key": google_maps_api_key,
            "now": datetime.datetime.now(),
        },
    )


@app.get("/about", response_class=HTMLResponse)
def about(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="about.html",
        context={
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
            state_lower = state.strip().casefold()
            sites = [site for site in sites if site.get("state") and state_lower == site["state"].casefold()]
        if site_type:
            sites = [site for site in sites if site.get("site_type") == site_type]

        return JSONResponse({"success": True, "count": len(sites), "sites": sites})
    except Exception as exc:
        logger.error("Error retrieving sites: %s", exc)
        return JSONResponse({"success": False, "error": "Unable to retrieve sites"}, status_code=500)


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
        return JSONResponse({"success": False, "error": "Unable to retrieve site"}, status_code=500)


@app.post("/api/import-data", dependencies=[Depends(require_admin)])
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
        return JSONResponse({"success": False, "error": "Unable to import site data"}, status_code=500)


@app.post("/api/clear-data", dependencies=[Depends(require_admin)])
def clear_data() -> JSONResponse:
    try:
        db_adapter = get_db()
        deleted_count = db_adapter.clear_sites()

        return JSONResponse(
            {
                "success": True,
                "message": f"Successfully deleted {deleted_count} Nike missile sites.",
            }
        )
    except Exception as exc:
        logger.error("Error clearing data: %s", exc)
        return JSONResponse({"success": False, "error": "Unable to clear site data"}, status_code=500)


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port)

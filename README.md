# Nike Missile Base Map (FastAPI)

Interactive map of US Nike missile control and launch locations, with data scraped from [Wikipedia](https://en.wikipedia.org/wiki/List_of_Nike_missile_sites).

## Local run

Use Python 3.12 or newer:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python main.py
```

Open `http://localhost:8000`. For development with reload:

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

The app initializes SQLite and automatically imports Wikipedia data when the database is empty. The first startup can take up to 30 seconds for the request. If the source is unavailable, the app starts with an empty map and reports the absence of data; retry with the authenticated import endpoint or `python import_sites.py`. Database initialization failures stop startup.

Set `AUTO_IMPORT_DATA=false` to skip the startup fetch. SQLite uses `DATABASE_PATH` (default `./nike_sites.db`). `DB_BACKEND=memory` is available for ephemeral, single-process use; its data does not persist or synchronize between workers. Imports replace the dataset atomically and reject empty input. Site IDs may change after a replacement. The standalone importer honors the same `.env`, `DATABASE_PATH`, and `DB_BACKEND` settings as the server.

## Map assets

Leaflet 1.9.4, its marker images, and generated Tailwind CSS are included in `app/static`. A normal Python deployment needs no JavaScript build step. OpenStreetMap tiles and optional Google Maps still require internet access. Google Maps loading/authentication failures fall back to Leaflet; Google fonts have system-font fallbacks.

After changing template classes, regenerate the committed stylesheet with Node 22 or newer:

```bash
npm ci
npm run build:css
```

Leaflet's license is retained in `app/static/vendor/leaflet/LICENSE`. The Tailwind build pins Parcel's watcher to a patched version through an npm override.

## Deployment (Coolify or Docker)

The included Dockerfile runs as an unprivileged user and respects `PORT` (default `8000`). Deploy this Git repository with Dockerfile detection, or build locally:

```bash
docker build -t nike-base-site .
docker run --rm -p 8000:8000 --env-file .env -e APP_ENV=production -e DATABASE_PATH=/data/nike_sites.db -v nike-data:/data nike-base-site
```

Attach a persistent volume at `/data`. Set:

- `APP_ENV=production`
- `DATABASE_PATH=/data/nike_sites.db`
- `ADMIN_API_TOKEN` to a strong private token
- `GOOGLE_MAPS_API_KEY` optionally; restrict this browser-visible key to your site's domain

The mounted directory must be writable by UID 10001 when using the Dockerfile. Without Docker, install `requirements.txt` and start with `python main.py`. Route the configured `PORT` to the service. `GET /healthz` reports database availability and is used by the container health check.

## API

- `GET /api/sites`: returns `success`, `count`, and `sites`. Optional `state` matches the complete state label, ignoring case and surrounding whitespace; `site_type` matches `Control` or `Launch` exactly. Some source rows retain a combined regional state label where their location does not identify one state.
- `GET /api/sites/{site_id}`: returns a site or HTTP 404.
- `POST /api/import-data`: refreshes the dataset; failure preserves existing records.
- `POST /api/clear-data`: deletes all records atomically.

Both POST endpoints require `Authorization: Bearer $ADMIN_API_TOKEN`. An absent configured token returns HTTP 503; incorrect credentials return HTTP 401. Clearing an empty dataset is safe. A subsequent startup with automatic import enabled repopulates an empty database.

```bash
curl -X POST http://localhost:8000/api/import-data \
  -H "Authorization: Bearer $ADMIN_API_TOKEN"
```

Each source coordinate is a separate control or launch location. Source names and descriptions come from the location and corresponding area columns; missing current status is reported as unknown. Rows without usable coordinates are omitted from scraped data. The browser also excludes invalid coordinates already present in older databases and shows their count. Existing databases keep their data until refreshed.

## Verification

```bash
pip install -r requirements-dev.txt
python -m pytest -q
python -m playwright install chromium
RUN_BROWSER_TESTS=1 python -m pytest -q
```

Tests use local fixtures and mocked network calls. Browser tests run a temporary server and exercise real Leaflet rendering, filtering, details, retry, empty data, Google-script fallback, and mobile layout. CI runs Python tests on 3.12 and 3.14, browser tests on 3.12, and verifies the generated CSS and npm audit.

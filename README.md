# Nike Missile Base Map (FastAPI)

Interactive web app that maps Nike missile sites across the US, with data scraped from Wikipedia.

## Tech Stack

- FastAPI
- Jinja2 templates
- SQLite
- BeautifulSoup scraper

## Local Run

1. Create and activate a virtualenv.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. (Optional) create `.env`:

```env
APP_ENV=development
GOOGLE_MAPS_API_KEY=your-google-maps-api-key
DATABASE_PATH=./nike_sites.db
```

4. Start the app:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000`.

## Render Deployment

This repo is configured for Render with the same settings as the official FastAPI example.

### Option A: Manual service setup

Use these values when creating a Render Web Service:

- Language: `Python 3`
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

Set environment variables in Render as needed:

- `APP_ENV=production`
- `GOOGLE_MAPS_API_KEY=...` (optional; app falls back to Leaflet/OpenStreetMap if missing)
- `DATABASE_PATH=/tmp/nike_sites.db` (default on Render if omitted)

### Option B: Blueprint (`render.yaml`)

This repo includes `render.yaml`, so you can deploy as a Blueprint directly from GitHub.

## API Endpoints

- `GET /api/sites`
- `GET /api/sites/{site_id}`
- `POST /api/import-data`
- `POST /api/clear-data`

## Notes

- Data is auto-imported from Wikipedia at startup if the database is empty.
- Render free instances use ephemeral storage unless you attach a persistent disk.

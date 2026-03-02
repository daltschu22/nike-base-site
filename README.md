# Nike Missile Base Map (FastAPI)

Interactive web app that maps Nike missile sites across the US, with data scraped from Wikipedia.

## Tech Stack

- FastAPI
- Jinja2 templates
- SQLite (persistent via Railway Volume)
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

## Railway Deployment (Persistent SQLite)

This repo is configured for Railway with:

- [`railway.toml`](./railway.toml)
- [`Procfile`](./Procfile)

### 1. Create service

- New Project -> Deploy from GitHub repo.

### 2. Attach a Volume

- In Railway service settings, add a Volume.
- Mount path example: `/data`.

### 3. Set environment variables

- `APP_ENV=production`
- `DATABASE_PATH=/data/nike_sites.db`
- `GOOGLE_MAPS_API_KEY=...` (optional; app falls back to Leaflet/OpenStreetMap if missing)

### 4. Deploy

Railway will run:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

## API Endpoints

- `GET /api/sites`
- `GET /api/sites/{site_id}`
- `POST /api/import-data`
- `POST /api/clear-data`

## Notes

- Data is auto-imported from Wikipedia at startup if the database is empty.
- Persistence depends on using a mounted Railway Volume for `DATABASE_PATH`.

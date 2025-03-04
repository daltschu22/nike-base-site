# Nike Missile Base Map

An interactive web application that displays the locations of Nike missile sites across the United States on a Google Maps interface.

## Project Overview

The Nike Missile Base Map is a Flask-based web application that:

- Displays all Nike missile base sites on an interactive Google Maps interface
- Shows information about each site when clicked
- Allows filtering of sites by state and site type
- Provides historical context about the Nike missile system
- Automatically scrapes data from Wikipedia to populate the database on first run

## Features

- Interactive Google Maps integration
- Automatic data scraping from Wikipedia
- Filtering and search capabilities
- Responsive design for desktop and mobile
- Detailed information about each missile site
- About page with historical context

## Prerequisites

- Python 3.8 or higher
- Podman (or Docker)
- Google Maps JavaScript API key

## Installation

### Clone the repository

```bash
git clone https://github.com/yourusername/nike-base-site.git
cd nike-base-site
```

### Set up environment variables

Create a `.env` file in the project root with the following variables:

```
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-secret-key
GOOGLE_MAPS_API_KEY=your-google-maps-api-key
```

Replace `your-secret-key` with a secure random string and `your-google-maps-api-key` with your Google Maps JavaScript API key.

### Using Podman

The project includes a Podman script for easy deployment:

```bash
# Start the application
./podman.sh start

# View logs
./podman.sh logs

# Stop the application
./podman.sh stop

# Show status
./podman.sh status
```

### Manual Setup (without Podman)

1. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the application:

```bash
flask run
```

## Deployment to Vercel

This application can be deployed to Vercel for hosting. The project includes configuration files for Vercel deployment.

### Prerequisites for Vercel Deployment

- [Vercel CLI](https://vercel.com/cli) installed
- A Vercel account

### Deployment Steps

1. Make sure you have the Vercel CLI installed:

```bash
npm i -g vercel
```

2. Use the included deployment script:

```bash
# Deploy to preview environment
./vercel.sh deploy

# Deploy to production
./vercel.sh deploy:prod

# View logs
./vercel.sh logs
```

3. Set up environment variables in the Vercel dashboard:
   - `FLASK_APP`: run.py
   - `FLASK_ENV`: production
   - `SECRET_KEY`: your-secret-key
   - `GOOGLE_MAPS_API_KEY`: your-google-maps-api-key
   - `VERCEL_ENV`: production

### Vercel Deployment Considerations

- **Read-only filesystem**: Vercel uses a read-only filesystem for serverless functions. The application is designed to handle this limitation by:
  - Avoiding any filesystem operations completely
  - Using in-memory storage for data when running on Vercel
  - Automatically loading data on startup without requiring file system writes
  - Not attempting to create any directories or files

### Database Considerations

The application uses different database adapters depending on the environment:

- For local development: SQLite database
- For Vercel deployment: In-memory database (data will be lost on server restarts)

The application includes code for Vercel KV integration, which can be enabled later for persistent storage:

1. Uncomment the vercel-kv dependency in requirements.txt
2. Update the get_db() function in app/database.py to use VercelKVAdapter
3. Set up Vercel KV in your Vercel project and add the required environment variables

## Usage

1. Start the application using one of the methods above
2. Open your browser and navigate to http://localhost:5000
3. The application will automatically load Nike missile site data from Wikipedia on first run
4. Explore the map and click on markers to view site details
5. Use the filters panel to narrow down sites by state or site type

## Getting a Google Maps API Key

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable the Google Maps JavaScript API
4. Create an API key with appropriate restrictions
5. Add the API key to your `.env` file

## Project Structure

```
nike-base-site/
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── routes.py
│   ├── scraper.py
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   └── templates/
│       ├── base.html
│       ├── index.html
│       └── about.html
├── config.py
├── requirements.txt
├── run.py
├── Dockerfile
├── podman.sh
├── vercel.sh
├── vercel.json
└── .vercelignore
```

## Data Source

The application scrapes data from the [Wikipedia List of Nike missile sites](https://en.wikipedia.org/wiki/List_of_Nike_missile_sites).

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Data sourced from Wikipedia contributors
- Built with Flask, SQLAlchemy, and Google Maps JavaScript API

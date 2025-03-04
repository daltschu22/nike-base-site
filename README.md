# Nike Missile Base Map

An interactive web application that displays the locations of Nike missile sites across the United States on a Google Maps interface.

## Project Overview

The Nike Missile Base Map is a Flask-based web application that:

- Displays all Nike missile base sites on an interactive Google Maps interface
- Shows information about each site when clicked
- Allows filtering of sites by state and site type
- Provides historical context about the Nike missile system
- Scrapes data from Wikipedia to populate the database

## Features

- Interactive Google Maps integration
- Data scraping from Wikipedia
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

## Usage

1. Start the application using one of the methods above
2. Open your browser and navigate to http://localhost:5000
3. Click the "Import Data" button to fetch Nike missile site data from Wikipedia
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
└── podman.sh
```

## Data Source

The application scrapes data from the [Wikipedia List of Nike missile sites](https://en.wikipedia.org/wiki/List_of_Nike_missile_sites).

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Data sourced from Wikipedia contributors
- Built with Flask, SQLAlchemy, and Google Maps JavaScript API

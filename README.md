
# Geospatial File Measurement API

A FastAPI backend that accepts KML files and ZIP archives containing
Shapefiles, extracts features, and calculates geometry measurements.

## Features

- Upload KML and Shapefile ZIP files
- Extract feature geometry and properties
- Calculate polygon area in square metres
- Calculate line length in metres
- Transform geometries to a projected CRS
- Retrieve file information and measurements
- Validate file types and handle missing resources

## Tech Stack

- Python
- FastAPI
- GeoPandas
- Shapely
- PyProj
- Uvicorn

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs for interactive API documentation.

## Endpoints

- `GET /health` — health check
- `POST /api/files/` — upload and process a file
- `GET /api/files/{file_id}/` — retrieve file information
- `GET /api/files/{file_id}/measurements/` — retrieve measurements

## Architecture

Routes handle HTTP requests. The geospatial service reads files,
extracts features, transforms coordinate systems, and calculates
measurements. Processed results are currently stored in memory.

## Learning

This project demonstrates REST APIs, file uploads, validation,
exception handling, geospatial processing, coordinate reference
systems, and JSON responses.

## Limitations and Future Scope

- In-memory storage resets when the server restarts.
- Add persistent storage using PostgreSQL/PostGIS.
- Add automated tests and file-size limits.
- Improve CRS selection for global datasets.
- Add authentication and deployment.

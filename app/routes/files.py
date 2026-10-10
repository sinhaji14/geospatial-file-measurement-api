
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.geospatial import process_file
import tempfile
import os
import uuid

router = APIRouter()

# Temporary in-memory storage
FILES = {}


@router.post("/api/files/", status_code=201)
async def upload_file(file: UploadFile = File(...)):
    filename = file.filename or ""

    if not filename.lower().endswith((".kml", ".zip")):
        raise HTTPException(
            status_code=400,
            detail="Only KML and ZIP files are supported"
        )

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(
                temp_dir, os.path.basename(filename)
            )

            with open(file_path, "wb") as f:
                f.write(await file.read())

            result = process_file(file_path, filename)

        file_id = str(uuid.uuid4())

        FILES[file_id] = {
            "id": file_id,
            "filename": filename,
            "status": "COMPLETED",
            **result,
        }

        return {
            "id": file_id,
            "filename": filename,
            "feature_count": result["feature_count"],
            "crs": result["crs"],
            "status": "COMPLETED",
        }

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Could not process file: {str(e)}"
        )


@router.get("/api/files/{file_id}/")
def get_file_info(file_id: str):
    file_data = FILES.get(file_id)

    if not file_data:
        raise HTTPException(
            status_code=404,
            detail="File not found"
        )

    return {
        "id": file_data["id"],
        "filename": file_data["filename"],
        "feature_count": file_data["feature_count"],
        "crs": file_data["crs"],
        "status": file_data["status"],
    }


@router.get("/api/files/{file_id}/measurements/")
def get_measurements(file_id: str):
    file_data = FILES.get(file_id)

    if not file_data:
        raise HTTPException(
            status_code=404,
            detail="File not found"
        )

    return {
        "file_id": file_id,
        "measurements": file_data["features"],
    }

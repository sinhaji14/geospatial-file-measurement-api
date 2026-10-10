
from fastapi import FastAPI
from app.routes.files import router

app = FastAPI(title="Geospatial File Measurement API")

app.include_router(router)


@app.get("/health")
def health_check():
    return {"status": "ok"}

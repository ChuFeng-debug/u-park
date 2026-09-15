from fastapi import FastAPI

from app.api.routes.auth import router as auth_router
from app.api.routes.parkings import router as parkings_router
from app.api.routes.places import router as places_router
from app.api.routes.zones import router as zones_router

app = FastAPI(title="U-Park API")

app.include_router(auth_router)
app.include_router(parkings_router)
app.include_router(zones_router)
app.include_router(places_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

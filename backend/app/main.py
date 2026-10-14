from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes.admin_reservations import router as admin_reservations_router
from app.api.routes.admin_utilisateurs import router as admin_utilisateurs_router
from app.api.routes.auth import router as auth_router
from app.api.routes.blocages import router as blocages_router
from app.api.routes.demandes_visiteurs import router as demandes_visiteurs_router
from app.api.routes.incidents import router as incidents_router
from app.api.routes.parkings import router as parkings_router
from app.api.routes.places import router as places_router
from app.api.routes.regles_acces import router as regles_acces_router
from app.api.routes.reservations import router as reservations_router
from app.api.routes.statistiques import router as statistiques_router
from app.api.routes.zones import router as zones_router
from app.core.config import settings
from app.services.exceptions import ServiceError

app = FastAPI(title="U-Park API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ServiceError)
def handle_service_error(_request: Request, exc: ServiceError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


app.include_router(auth_router)
app.include_router(parkings_router)
app.include_router(zones_router)
app.include_router(places_router)
app.include_router(reservations_router)
app.include_router(demandes_visiteurs_router)
app.include_router(incidents_router)
app.include_router(blocages_router)
app.include_router(regles_acces_router)
app.include_router(admin_reservations_router)
app.include_router(statistiques_router)
app.include_router(admin_utilisateurs_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

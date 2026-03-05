"""FichaFacil MVP - Routers Package"""
from app.routers.auth import router as auth_router
from app.routers.negocios import router as negocios_router
from app.routers.fichajes import router as fichajes_router
from app.routers.correcciones import router as correcciones_router
from app.routers.pdf import router as pdf_router

__all__ = [
    "auth_router",
    "negocios_router",
    "fichajes_router",
    "correcciones_router",
    "pdf_router"
]

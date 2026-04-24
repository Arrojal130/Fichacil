"""
FichaFacil MVP - Main Application
FastAPI application with all routers and SSE realtime support.
"""
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import AsyncGenerator
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sse_starlette.sse import EventSourceResponse
from app.config import get_settings
from app.database import init_db, close_db
from app.models.user import User
from app.routers import (
    auth_router,
    negocios_router,
    fichajes_router,
    correcciones_router,
    pdf_router
)
from app.utils.security import get_current_user

settings = get_settings()

# SSE connections store
sse_connections: dict[int, list[asyncio.Queue]] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    await init_db()
    print("✅ Database initialized")
    yield
    # Shutdown
    await close_db()
    print("👋 Database connection closed")


app = FastAPI(
    title=settings.app_name,
    description="MVP diseñado para ayudar al registro horario de negocios",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
)

# CORS configuration for local development and deployed frontends
origins = settings.effective_allowed_origins
origin_regex = settings.cors_origin_regex

if origin_regex:
    print("🔌 CORS: Debug mode - Accepting RFC1918 LAN IPs on port 3000")

print(f"🔌 CORS explicit origins: {origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=origin_regex,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# Include routers
app.include_router(auth_router)
app.include_router(negocios_router)
app.include_router(fichajes_router)
app.include_router(correcciones_router)
app.include_router(pdf_router)


# === SSE Realtime ===

async def event_generator(
    request: Request,
    negocio_id: int
) -> AsyncGenerator:
    """Generate SSE events for realtime dashboard updates."""
    queue: asyncio.Queue = asyncio.Queue()
    
    # Register connection
    if negocio_id not in sse_connections:
        sse_connections[negocio_id] = []
    sse_connections[negocio_id].append(queue)
    
    try:
        # Send initial ping
        yield {
            "event": "connected",
            "data": f"Connected to FichaFacil realtime for negocio {negocio_id}"
        }
        
        while True:
            # Check if client disconnected
            if await request.is_disconnected():
                break
            
            try:
                # Wait for new event with timeout
                event = await asyncio.wait_for(queue.get(), timeout=30.0)
                yield event
            except asyncio.TimeoutError:
                # Send keepalive ping
                yield {
                    "event": "ping",
                    "data": datetime.now(timezone.utc).isoformat()
                }
    finally:
        # Cleanup connection
        if negocio_id in sse_connections:
            sse_connections[negocio_id].remove(queue)
            if not sse_connections[negocio_id]:
                del sse_connections[negocio_id]


def authorize_sse_access(*, current_user: User, negocio_id: int) -> None:
    """Ensure SSE subscriptions stay within the authenticated user's business."""
    if current_user.negocio_id != negocio_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No autorizado para acceder al canal de este negocio"
        )


@app.get("/sse/{negocio_id}")
async def sse_endpoint(
    request: Request,
    negocio_id: int,
    current_user: User = Depends(get_current_user),
):
    """
    SSE endpoint for realtime dashboard updates.
    
    Clients connect and receive events when:
    - New fichaje is created
    - Fichaje is corrected
    - Alerts are generated
    """
    authorize_sse_access(current_user=current_user, negocio_id=negocio_id)
    return EventSourceResponse(event_generator(request, negocio_id))


async def broadcast_to_negocio(negocio_id: int, event_type: str, data: dict):
    """Broadcast an event to all SSE clients for a business."""
    if negocio_id not in sse_connections:
        return
    
    import json
    event = {
        "event": event_type,
        "data": json.dumps(data)
    }
    
    for queue in sse_connections[negocio_id]:
        await queue.put(event)


# === Health Check ===

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0"
    }


# === Root Redirect ===

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with basic info."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>FichaFácil API</title>
        <style>
            body { font-family: system-ui; max-width: 600px; margin: 50px auto; padding: 20px; }
            h1 { color: #2563eb; }
            a { color: #2563eb; }
            code { background: #f3f4f6; padding: 2px 6px; border-radius: 4px; }
        </style>
    </head>
    <body>
        <h1>🕐 FichaFácil API</h1>
        <p>MVP diseñado para ayudar al registro horario de negocios.</p>
        <ul>
            <li><a href="/health">❤️ Health Check</a></li>
        </ul>
        <p><small>Versión 1.0.0 | Pendiente de validación legal definitiva</small></p>
    </body>
    </html>
    """


# Export broadcast function for use in routers
app.state.broadcast = broadcast_to_negocio
# Trigger reload

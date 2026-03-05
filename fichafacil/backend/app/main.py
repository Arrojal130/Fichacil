"""
FichaFacil MVP - Main Application
FastAPI application with all routers and SSE realtime support.
"""
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import AsyncGenerator
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sse_starlette.sse import EventSourceResponse
from app.config import get_settings
from app.database import init_db, close_db
from app.routers import (
    auth_router,
    negocios_router,
    fichajes_router,
    correcciones_router,
    pdf_router
)

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
    description="MVP de registro horario legal para negocios",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration for iPhone + LAN + Local dev
origins = settings.allowed_origins.split(",")

# In debug mode, also allow any LAN IP (192.168.x.x, 10.x.x.x) on port 3000
if settings.debug:
    import re
    # Add regex patterns for common LAN IPs
    origins.extend([
        re.compile(r"http://192\.168\.\d+\.\d+:3000"),  # 192.168.x.x
        re.compile(r"http://10\.\d+\.\d+\.\d+:3000"),   # 10.x.x.x
        re.compile(r"http://172\.\d+\.\d+\.\d+:3000"),  # 172.x.x.x
    ])
    print(f"🔌 CORS: Debug mode - Accepting any LAN IP on port 3000")

print(f"🔌 CORS explicit origins: {[o for o in origins if isinstance(o, str)]}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Mix of strings and regex patterns
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


@app.get("/sse/{negocio_id}")
async def sse_endpoint(request: Request, negocio_id: int):
    """
    SSE endpoint for realtime dashboard updates.
    
    Clients connect and receive events when:
    - New fichaje is created
    - Fichaje is corrected
    - Alerts are generated
    """
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
        <p>MVP de registro horario legal para negocios.</p>
        <ul>
            <li><a href="/docs">📚 Documentación API (Swagger)</a></li>
            <li><a href="/redoc">📖 Documentación API (ReDoc)</a></li>
            <li><a href="/health">❤️ Health Check</a></li>
        </ul>
        <p><small>Versión 1.0.0 | RD 318/2021 compliant</small></p>
    </body>
    </html>
    """


# Export broadcast function for use in routers
app.state.broadcast = broadcast_to_negocio
# Trigger reload

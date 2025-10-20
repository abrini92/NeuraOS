"""
Central FastAPI application.

This is the main entry point for the Neura API. All modules register
their routes here.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from neura import __version__
from neura.core.config import get_settings
from neura.core.events import get_event_bus
from neura.core.exceptions import NeuraError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Application lifespan manager.

    Handles startup and shutdown tasks like starting the event bus.
    """
    # Startup
    logger.info("Starting NeuraCore...")
    settings = get_settings()
    logger.info(f"Configuration loaded: data_dir={settings.data_dir}")

    # Start event bus
    event_bus = get_event_bus()
    await event_bus.start()

    yield

    # Shutdown
    logger.info("Shutting down NeuraCore...")
    await event_bus.stop()


# Create FastAPI app
app = FastAPI(
    title="Neura Core API",
    description="Local-first Cognitive Operating System",
    version=__version__,
    lifespan=lifespan,
)

# Add CORS middleware (for local development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handler for Neura errors
@app.exception_handler(NeuraError)
async def neura_error_handler(request: Request, exc: NeuraError) -> JSONResponse:
    """Handle Neura-specific exceptions."""
    logger.error(f"NeuraError: {exc.message}", extra={"details": exc.details})
    return JSONResponse(
        status_code=500,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "details": exc.details,
        },
    )


# Root endpoint
@app.get("/")
async def root() -> dict:
    """
    Root endpoint - health check.

    Returns:
        dict: Status and version information
    """
    return {
        "status": "alive",
        "message": "NeuraCore operational",
        "version": __version__,
    }


@app.get("/health")
async def health() -> dict:
    """
    Health check endpoint.

    Returns:
        dict: Detailed health status
    """
    settings = get_settings()

    # Check Cortex status
    from neura.cortex.engine import get_ollama_client
    from neura.cortex.types import CortexConfig

    cortex_status = "loaded"
    try:
        client = get_ollama_client(CortexConfig())
        ollama_status = await client.check_status()
        if not ollama_status.available:
            cortex_status = "loaded_but_ollama_unavailable"
    except Exception:
        cortex_status = "loaded_but_error"

    # Check Memory status
    from neura.memory.graph import get_memory_graph

    memory_status = "loaded"
    try:
        graph = get_memory_graph()
        if not graph._initialized:
            await graph.initialize()
        if not graph._qdrant_available:
            memory_status = "loaded_degraded_mode"
    except Exception:
        memory_status = "loaded_but_error"

    # Check Vault status
    from neura.vault.manager import get_vault_manager

    vault_status = "loaded"
    try:
        manager = get_vault_manager()
        status = manager.get_status()
        if status.state.value == "locked":
            vault_status = "loaded_locked"
        elif status.state.value == "unlocked":
            vault_status = "loaded_unlocked"
        elif status.state.value == "panic":
            vault_status = "panic_mode"
    except Exception:
        vault_status = "loaded_but_error"

    # Check Motor status
    motor_status = "loaded"
    try:
        from neura.motor.executor import get_motor_executor

        executor = get_motor_executor()
        if executor.dry_run:
            motor_status = "loaded_dry_run"
    except Exception:
        motor_status = "loaded_but_error"

    # Check Policy status
    policy_status = "loaded"
    try:
        from neura.policy.engine import get_policy_engine

        engine = get_policy_engine()
        if not engine.opa_available:
            policy_status = "loaded_fallback"
    except Exception:
        policy_status = "loaded_but_error"

    return {
        "status": "healthy",
        "version": __version__,
        "debug": settings.debug,
        "modules": {
            "cortex": cortex_status,
            "memory": memory_status,
            "vault": vault_status,
            "motor": motor_status,
            "policy": policy_status,
        },
    }


# Module routers
from neura.core.why_router import router as why_router
from neura.cortex import router as cortex_router
from neura.memory import router as memory_router
from neura.motor.router import router as motor_router
from neura.policy.router import router as policy_router
from neura.vault import router as vault_router
from neura.voice.router import router as voice_router

app.include_router(cortex_router, prefix="/api/cortex", tags=["cortex"])
app.include_router(memory_router, prefix="/api/memory", tags=["memory"])
app.include_router(vault_router, prefix="/api/vault", tags=["vault"])
app.include_router(motor_router, prefix="/api/motor", tags=["motor"])
app.include_router(policy_router, prefix="/api/policy", tags=["policy"])
app.include_router(why_router, prefix="/api/why", tags=["why"])
app.include_router(voice_router, prefix="/api/voice", tags=["voice"])


def main() -> None:
    """
    Main entry point for running the API directly.

    This is used by the Poetry script: `poetry run neura`
    """
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "neura.core.api:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()

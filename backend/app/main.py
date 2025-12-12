"""
FastAPI application entry point.
Configures CORS, middleware, exception handlers, and includes all routers.
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.config import get_settings
from app.database import init_db, close_db
from app.metrics import setup_metrics
from app.logging_config import setup_request_logging

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup and shutdown events."""
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API for detecting gambling comments on YouTube videos using ML",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    redirect_slashes=False,  # Prevent 307 redirects that cause mixed-content issues
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception Handlers
@app.exception_handler(ValidationError)
async def validation_exception_handler(
    request: Request, exc: ValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "error_code": "validation_error",
            "message": "Request validation failed",
            "details": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Handle unexpected exceptions."""
    if settings.debug:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "error_code": "internal_error",
                "message": str(exc),
                "details": None,
            },
        )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "error_code": "internal_error",
            "message": "An unexpected error occurred",
            "details": None,
        },
    )


# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "version": settings.app_version}


# Root endpoint
@app.get("/", tags=["root"])
async def root() -> dict:
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs" if settings.debug else "Disabled in production",
    }


# Include routers
from app.routers import auth, prediction, scan, youtube, dashboard, validation, model
app.include_router(auth.router)
app.include_router(prediction.router)
app.include_router(scan.router)
app.include_router(youtube.router)
app.include_router(dashboard.router)
app.include_router(validation.router)
app.include_router(model.router)

# Setup Prometheus metrics
setup_metrics(app)

# Setup structured JSON logging
setup_request_logging(app, log_level="INFO" if not settings.debug else "DEBUG")

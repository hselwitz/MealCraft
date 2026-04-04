"""MealCraft FastAPI application."""

import logging
from contextlib import asynccontextmanager

from app.config import settings
from app.db import init_db
from app.routers import (
    plans_router,
    recipes_router,
    leftovers_router,
    grocery_router,
    feedback_router,
    settings_router,
)
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting MealCraft backend...")
    await init_db()
    logger.info("Database initialized.")
    yield
    logger.info("Shutting down MealCraft backend.")


app = FastAPI(
    title="MealCraft API",
    version="0.1.0",
    description="AI-powered meal planning assistant",
    lifespan=lifespan,
)

# CORS - permissive for dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# RFC 7807 Problem Details exception handler
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "type": "about:blank",
            "title": "Internal Server Error",
            "status": 500,
            "detail": str(exc),
            "instance": str(request.url),
        },
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "type": "about:blank",
            "title": "Not Found",
            "status": 404,
            "detail": "The requested resource was not found.",
            "instance": str(request.url),
        },
    )


# Health check
@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}


# Routers
app.include_router(plans_router, prefix="/api")
app.include_router(recipes_router, prefix="/api")
app.include_router(leftovers_router, prefix="/api")
app.include_router(grocery_router, prefix="/api")
app.include_router(feedback_router, prefix="/api")
app.include_router(settings_router, prefix="/api")

# Serve frontend — only mounted when the built static files are present (i.e. in Docker)
_static_dir = Path("/app/static")
if _static_dir.exists():
    app.mount("/", StaticFiles(directory=_static_dir, html=True), name="static")

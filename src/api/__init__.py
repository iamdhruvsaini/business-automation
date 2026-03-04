"""
Clara Pipeline API
==================
FastAPI application with modular routers.

Run: uvicorn src.api:app --host 0.0.0.0 --port 8000
"""
from fastapi import FastAPI

from src.api.routers import (
    health_router,
    pipeline_router,
    accounts_router,
    dataset_router,
    db_router,
)

app = FastAPI(
    title="Clara Pipeline API",
    description="n8n-orchestrated automation pipeline for Retell agent generation",
    version="0.1.0",
)

# Include all routers
app.include_router(health_router)
app.include_router(pipeline_router)
app.include_router(accounts_router)
app.include_router(dataset_router)
app.include_router(db_router)


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "Clara Pipeline API",
        "version": "0.1.0",
        "docs": "/docs",
        "endpoints": {
            "health": "/health",
            "pipeline": "/pipeline/demo, /pipeline/onboarding, /pipeline/full",
            "accounts": "/accounts, /accounts/{id}, /accounts/{id}/diff",
            "dataset": "/dataset",
        },
    }

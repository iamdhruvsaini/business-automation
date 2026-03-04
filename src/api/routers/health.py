"""
Health Check Router
===================
Health check endpoints for service monitoring.
"""
from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """Health check endpoint for n8n."""
    return {"status": "ok", "service": "agent-pipeline"}

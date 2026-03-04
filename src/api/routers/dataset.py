"""
Dataset Router
==============
Endpoints for listing available transcripts in the dataset.
"""
from fastapi import APIRouter

from src.config import get_dataset_path

router = APIRouter(prefix="/dataset", tags=["Dataset"])


@router.get("")
async def list_dataset():
    """List available transcripts in dataset."""
    demo_path = get_dataset_path("demo")
    onboarding_path = get_dataset_path("onboarding")
    
    demos = [f.stem.replace("_demo", "") for f in demo_path.glob("*.txt")] if demo_path.exists() else []
    onboarding = [f.stem.replace("_onboarding", "") for f in onboarding_path.glob("*.txt")] if onboarding_path.exists() else []
    
    return {
        "demo_transcripts": demos,
        "onboarding_transcripts": onboarding,
        "demo_count": len(demos),
        "onboarding_count": len(onboarding),
    }

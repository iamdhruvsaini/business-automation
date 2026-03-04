"""
Pipeline Router
===============
Endpoints for running demo and onboarding pipelines.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.config import get_dataset_path, get_output_path, logger
from src.extractors.demo import DemoExtractor, process_all_demos
from src.extractors.onboarding import OnboardingProcessor, process_all_onboarding
from src.generators.agent_spec import generate_all_specs, generate_for_account

router = APIRouter(prefix="/pipeline", tags=["Pipeline"])


class ProcessResponse(BaseModel):
    """Response model for processing endpoints."""
    status: str
    processed: int
    accounts: list[str]
    message: str


class AccountResponse(BaseModel):
    """Response model for single account operations."""
    status: str
    account_id: str
    version: str
    message: str


# ============ PIPELINE A: DEMO PROCESSING ============


@router.post("/demo", response_model=ProcessResponse)
async def run_demo_pipeline(force: bool = False):
    """
    Pipeline A: Process all demo call transcripts.
    Generates v1 account memos and agent specs.
    
    Query params:
        force: If true, reprocess even if output exists.
    """
    try:
        logger.info(f"n8n triggered: Pipeline A (Demo Processing, force={force})")
        results = process_all_demos(force=force)
        generate_all_specs()
        
        accounts = [r["account_id"] for r in results]
        return ProcessResponse(
            status="success",
            processed=len(results),
            accounts=accounts,
            message=f"Processed {len(results)} demo calls, generated v1 specs",
        )
    except Exception as e:
        logger.error(f"Pipeline A failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/demo/{account_id}", response_model=AccountResponse)
async def process_single_demo(account_id: str):
    """Process a single demo transcript by account ID."""
    try:
        demo_path = get_dataset_path("demo")
        transcript_file = demo_path / f"{account_id}_demo.txt"
        
        if not transcript_file.exists():
            raise HTTPException(status_code=404, detail=f"Demo transcript not found: {account_id}")
        
        extractor = DemoExtractor()
        memo = extractor.process_file(transcript_file)
        
        if memo:
            generate_for_account(account_id, "v1")
            return AccountResponse(
                status="success",
                account_id=account_id,
                version="v1",
                message=f"Generated v1 for {memo['company_name']}",
            )
        else:
            raise HTTPException(status_code=500, detail="Extraction failed")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Demo processing failed for {account_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ PIPELINE B: ONBOARDING PROCESSING ============


@router.post("/onboarding", response_model=ProcessResponse)
async def run_onboarding_pipeline(force: bool = False):
    """
    Pipeline B: Process all onboarding call transcripts.
    Updates v1 to v2 with changelog.
    
    Query params:
        force: If true, reprocess even if output exists.
    """
    try:
        logger.info(f"n8n triggered: Pipeline B (Onboarding Processing, force={force})")
        results = process_all_onboarding(force=force)
        generate_all_specs()
        
        accounts = [r["account_id"] for r in results]
        return ProcessResponse(
            status="success",
            processed=len(results),
            accounts=accounts,
            message=f"Processed {len(results)} onboarding calls, generated v2 specs",
        )
    except Exception as e:
        logger.error(f"Pipeline B failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/onboarding/{account_id}", response_model=AccountResponse)
async def process_single_onboarding(account_id: str):
    """Process a single onboarding transcript by account ID."""
    try:
        onboarding_path = get_dataset_path("onboarding")
        transcript_file = onboarding_path / f"{account_id}_onboarding.txt"
        
        if not transcript_file.exists():
            raise HTTPException(status_code=404, detail=f"Onboarding transcript not found: {account_id}")
        
        # Check v1 exists
        v1_path = get_output_path(account_id, "v1")
        if not (v1_path / "account_memo.json").exists():
            raise HTTPException(status_code=400, detail=f"No v1 found for {account_id}. Run demo first.")
        
        processor = OnboardingProcessor()
        memo = processor.process_file(transcript_file)
        
        if memo:
            generate_for_account(account_id, "v2")
            return AccountResponse(
                status="success",
                account_id=account_id,
                version="v2",
                message=f"Generated v2 for {memo['company_name']}",
            )
        else:
            raise HTTPException(status_code=500, detail="Update extraction failed")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Onboarding processing failed for {account_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ FULL PIPELINE ============


@router.post("/full", response_model=ProcessResponse)
async def run_full_pipeline(force: bool = False):
    """
    Run complete pipeline: Demo → v1 → Onboarding → v2.
    
    Query params:
        force: If true, reprocess even if outputs exist.
    """
    try:
        logger.info(f"n8n triggered: Full Pipeline (force={force})")
        
        # Pipeline A
        demo_results = process_all_demos(force=force)
        generate_all_specs()
        
        # Pipeline B
        onboarding_results = process_all_onboarding(force=force)
        generate_all_specs()
        
        all_accounts = list(set(
            [r["account_id"] for r in demo_results] +
            [r["account_id"] for r in onboarding_results]
        ))
        
        return ProcessResponse(
            status="success",
            processed=len(demo_results) + len(onboarding_results),
            accounts=all_accounts,
            message=f"Full pipeline complete: {len(demo_results)} demos, {len(onboarding_results)} onboarding",
        )
    except Exception as e:
        logger.error(f"Full pipeline failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

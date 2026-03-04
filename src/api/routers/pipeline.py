"""
Pipeline Router
===============
Endpoints for running demo and onboarding pipelines.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.config import get_dataset_path, get_output_path, logger
from src.extractors.demo import DemoExtractor, process_all_demos
from src.extractors.onboarding import OnboardingProcessor, process_all_onboarding
from src.generators.agent_spec import generate_all_specs, generate_for_account, generate_agent_spec
from src.utils import save_json, load_json, get_timestamp
from src.db import get_memo as db_get_memo

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


# ============ INPUT MODELS FOR DIRECT TRANSCRIPT PROCESSING ============


class DemoTranscriptInput(BaseModel):
    """Input model for processing demo transcript directly."""
    account_id: str = Field(..., description="Unique account identifier")
    transcript: str = Field(..., description="Full demo call transcript text")


class OnboardingTranscriptInput(BaseModel):
    """Input model for processing onboarding transcript directly."""
    account_id: str = Field(..., description="Unique account identifier")
    transcript: str = Field(..., description="Full onboarding call transcript text")
    v1_memo: Optional[dict] = Field(default=None, description="Provide v1 memo if not saved on disk")


class FullTranscriptInput(BaseModel):
    """Input model for full pipeline with both transcripts."""
    account_id: str = Field(..., description="Unique account identifier")
    demo_transcript: str = Field(..., description="Demo call transcript")
    onboarding_transcript: Optional[str] = Field(default=None, description="Onboarding transcript (optional)")


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


# ============ DIRECT TRANSCRIPT INPUT (FOR N8N WEBHOOKS) ============


@router.post("/process/demo")
async def process_demo_direct(input_data: DemoTranscriptInput):
    """
    Process demo transcript sent directly in request body.
    
    Use this endpoint when sending transcript text from n8n webhook.
    Returns full account memo and agent spec.
    """
    try:
        logger.info(f"Processing demo transcript for: {input_data.account_id}")
        
        extractor = DemoExtractor()
        extracted = extractor.extract(input_data.transcript)
        
        if not extracted:
            raise HTTPException(status_code=500, detail="Failed to extract data from transcript")
        
        memo = extractor.build_memo(extracted, input_data.account_id)
        spec = generate_agent_spec(memo)
        
        # Save to disk (local backup)
        output_path = get_output_path(input_data.account_id, "v1")
        save_json(memo, output_path / "account_memo.json")
        save_json(extracted.model_dump(), output_path / "raw_extraction.json")
        save_json(spec, output_path / "retell_agent_spec.json")
        
        return {
            "status": "success",
            "account_id": input_data.account_id,
            "version": "v1",
            "company_name": memo.get("company_name"),
            "account_memo": memo,
            "agent_spec": spec,
            "message": f"Demo processed for {memo.get('company_name')}",
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Demo processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process/onboarding")
async def process_onboarding_direct(input_data: OnboardingTranscriptInput):
    """
    Process onboarding transcript sent directly in request body.
    
    Use this endpoint when sending transcript text from n8n webhook.
    Requires v1 to exist (or provide v1_memo in request).
    Returns updated v2 memo, changelog, and agent spec.
    """
    try:
        logger.info(f"Processing onboarding transcript for: {input_data.account_id}")
        
        # Get v1 memo - check request first, then MongoDB, then disk
        if input_data.v1_memo:
            v1_memo = input_data.v1_memo
        else:
            # Try MongoDB first
            v1_memo = db_get_memo(input_data.account_id, "v1")
            
            if not v1_memo:
                # Fall back to disk
                v1_path = get_output_path(input_data.account_id, "v1")
                v1_memo_file = v1_path / "account_memo.json"
                
                if not v1_memo_file.exists():
                    raise HTTPException(
                        status_code=400,
                        detail=f"No v1 found for {input_data.account_id}. Run demo first or provide v1_memo."
                    )
                v1_memo = load_json(v1_memo_file)
        
        processor = OnboardingProcessor()
        updates = processor.extract_updates(input_data.transcript, v1_memo)
        
        if not updates:
            raise HTTPException(status_code=500, detail="Failed to extract updates from transcript")
        
        v2_memo = processor.apply_updates(v1_memo, updates)
        changelog = processor.generate_changelog(v1_memo, v2_memo, updates.changes_summary)
        spec = generate_agent_spec(v2_memo)
        
        # Save to disk (local backup)
        output_path = get_output_path(input_data.account_id, "v2")
        save_json(v2_memo, output_path / "account_memo.json")
        save_json(updates.model_dump(), output_path / "raw_updates.json")
        save_json(changelog, output_path / "changelog.json")
        save_json(spec, output_path / "retell_agent_spec.json")
        
        return {
            "status": "success",
            "account_id": input_data.account_id,
            "version": "v2",
            "company_name": v2_memo.get("company_name"),
            "account_memo": v2_memo,
            "changelog": changelog,
            "agent_spec": spec,
            "raw_extraction": updates.model_dump(),
            "message": f"Onboarding processed - {len(changelog.get('changes', []))} changes applied",
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Onboarding processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process/full")
async def process_full_direct(input_data: FullTranscriptInput):
    """
    Process both demo and onboarding transcripts in one request.
    
    Use this endpoint when you have both transcripts available.
    Returns final v2 (or v1 if no onboarding transcript provided).
    """
    try:
        logger.info(f"Processing full pipeline for: {input_data.account_id}")
        
        # Step 1: Process demo
        extractor = DemoExtractor()
        demo_extracted = extractor.extract(input_data.demo_transcript)
        
        if not demo_extracted:
            raise HTTPException(status_code=500, detail="Failed to extract demo data")
        
        v1_memo = extractor.build_memo(demo_extracted, input_data.account_id)
        v1_spec = generate_agent_spec(v1_memo)
        
        # Save v1 to disk (local backup)
        v1_path = get_output_path(input_data.account_id, "v1")
        save_json(v1_memo, v1_path / "account_memo.json")
        save_json(demo_extracted.model_dump(), v1_path / "raw_extraction.json")
        save_json(v1_spec, v1_path / "retell_agent_spec.json")
        
        # If no onboarding, return v1
        if not input_data.onboarding_transcript:
            return {
                "status": "success",
                "account_id": input_data.account_id,
                "version": "v1",
                "company_name": v1_memo.get("company_name"),
                "account_memo": v1_memo,
                "agent_spec": v1_spec,
                "raw_extraction": demo_extracted.model_dump(),
                "message": "Demo processed (no onboarding transcript provided)",
            }
        
        # Step 2: Process onboarding
        processor = OnboardingProcessor()
        updates = processor.extract_updates(input_data.onboarding_transcript, v1_memo)
        
        if not updates:
            raise HTTPException(status_code=500, detail="Failed to extract onboarding updates")
        
        v2_memo = processor.apply_updates(v1_memo, updates)
        changelog = processor.generate_changelog(v1_memo, v2_memo, updates.changes_summary)
        v2_spec = generate_agent_spec(v2_memo)
        
        # Save v2 to disk (local backup)
        v2_path = get_output_path(input_data.account_id, "v2")
        save_json(v2_memo, v2_path / "account_memo.json")
        save_json(updates.model_dump(), v2_path / "raw_updates.json")
        save_json(changelog, v2_path / "changelog.json")
        save_json(v2_spec, v2_path / "retell_agent_spec.json")
        
        return {
            "status": "success",
            "account_id": input_data.account_id,
            "version": "v2",
            "company_name": v2_memo.get("company_name"),
            "account_memo": v2_memo,
            "changelog": changelog,
            "agent_spec": v2_spec,
            "raw_extraction": updates.model_dump(),
            "message": f"Full pipeline complete - {len(changelog.get('changes', []))} changes applied",
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Full pipeline failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

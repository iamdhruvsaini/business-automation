"""
Database Router - API endpoints for MongoDB operations.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException

from src.db import SaveRequest, save_account as db_save, get_account as db_get, get_memo, list_accounts as db_list, delete_account as db_delete, db_health
from src.config import logger

router = APIRouter(prefix="/db", tags=["Database"])


@router.get("/health")
async def health():
    """Check MongoDB connection."""
    return db_health()


@router.post("/save")
async def save(data: SaveRequest):
    """Save account data (called by n8n workflow)."""
    try:
        result = db_save(data)
        return {"status": "success", **result}
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail="Database not available")
    except Exception as e:
        logger.error(f"DB save failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/accounts")
async def list_all():
    """List all accounts."""
    accounts = db_list()
    return {"count": len(accounts), "accounts": accounts}


@router.get("/accounts/{account_id}")
async def get(account_id: str, version: str = "v1"):
    """Get account data."""
    account = db_get(account_id, version)
    if not account:
        raise HTTPException(status_code=404, detail=f"{account_id} {version} not found")
    return {"account": account}


@router.get("/accounts/{account_id}/memo")
async def memo(account_id: str, version: str = "v1"):
    """Get account memo."""
    memo = get_memo(account_id, version)
    if not memo:
        raise HTTPException(status_code=404, detail=f"{account_id} {version} not found")
    return {"account_memo": memo}


@router.delete("/accounts/{account_id}")
async def delete(account_id: str, version: Optional[str] = None):
    """Delete account."""
    deleted = db_delete(account_id, version)
    if deleted == 0:
        raise HTTPException(status_code=404, detail=f"{account_id} not found")
    return {"deleted_count": deleted}

"""
Accounts Router
===============
Endpoints for retrieving account data and comparisons.
"""
from fastapi import APIRouter, HTTPException

from src.config import get_output_path, get_all_accounts
from src.utils import load_json

router = APIRouter(prefix="/accounts", tags=["Accounts"])


@router.get("")
async def list_accounts():
    """List all processed accounts."""
    accounts = get_all_accounts()
    return {"accounts": accounts, "count": len(accounts)}


@router.get("/{account_id}")
async def get_account(account_id: str, version: str = "v1"):
    """Get account memo and agent spec."""
    try:
        output_path = get_output_path(account_id, version)
        memo_file = output_path / "account_memo.json"
        spec_file = output_path / "retell_agent_spec.json"
        
        if not memo_file.exists():
            raise HTTPException(status_code=404, detail=f"Account {account_id}/{version} not found")
        
        response = {
            "account_id": account_id,
            "version": version,
            "memo": load_json(memo_file),
        }
        
        if spec_file.exists():
            response["agent_spec"] = load_json(spec_file)
        
        # Include changelog for v2
        if version == "v2":
            changelog_file = output_path / "changelog.json"
            if changelog_file.exists():
                response["changelog"] = load_json(changelog_file)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{account_id}/diff")
async def get_account_diff(account_id: str):
    """Get v1 vs v2 comparison for an account."""
    try:
        v1_path = get_output_path(account_id, "v1")
        v2_path = get_output_path(account_id, "v2")
        
        v1_memo = v1_path / "account_memo.json"
        v2_memo = v2_path / "account_memo.json"
        changelog = v2_path / "changelog.json"
        
        if not v1_memo.exists():
            raise HTTPException(status_code=404, detail=f"No v1 found for {account_id}")
        
        response = {
            "account_id": account_id,
            "v1": load_json(v1_memo),
            "v2": load_json(v2_memo) if v2_memo.exists() else None,
            "changelog": load_json(changelog) if changelog.exists() else None,
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

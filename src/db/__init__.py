"""
Database Module - Simple MongoDB operations
"""
from typing import Optional
from datetime import datetime
from pymongo import MongoClient
from pydantic import BaseModel, Field

from src.config import MONGODB_URI, MONGODB_DATABASE, logger


# ============ CONNECTION ============

_client: Optional[MongoClient] = None
_db = None


def get_db():
    """Get MongoDB database instance."""
    global _client, _db
    if _client is None:
        try:
            _client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
            _db = _client[MONGODB_DATABASE]
            _client.admin.command('ping')
            logger.info(f"MongoDB connected: {MONGODB_DATABASE}")
        except Exception as e:
            logger.error(f"MongoDB connection failed: {e}")
            return None
    return _db


def db_health() -> dict:
    """Check MongoDB health."""
    db = get_db()
    if db is not None:
        return {"status": "healthy", "database": MONGODB_DATABASE}
    return {"status": "unhealthy", "error": "Not connected"}


# ============ MODELS ============

class SaveRequest(BaseModel):
    """Request to save account data."""
    account_id: str
    version: str
    company_name: Optional[str] = None
    account_memo: dict
    agent_spec: dict
    raw_extraction: Optional[dict] = None
    changelog: Optional[dict] = None
    pipeline_type: str = "demo"


# ============ CRUD OPERATIONS ============

def save_account(data: SaveRequest) -> dict:
    """Save or update account in MongoDB."""
    db = get_db()
    if db is None:
        raise ConnectionError("MongoDB not connected")
    
    doc = {
        "account_id": data.account_id,
        "version": data.version,
        "company_name": data.company_name,
        "account_memo": data.account_memo,
        "agent_spec": data.agent_spec,
        "pipeline_type": data.pipeline_type,
        "updated_at": datetime.utcnow(),
    }
    if data.raw_extraction:
        doc["raw_extraction"] = data.raw_extraction
    if data.changelog:
        doc["changelog"] = data.changelog
    
    result = db.accounts.update_one(
        {"account_id": data.account_id, "version": data.version},
        {"$set": doc, "$setOnInsert": {"created_at": datetime.utcnow()}},
        upsert=True
    )
    
    logger.info(f"Saved {data.account_id} {data.version}")
    return {"status": "saved", "account_id": data.account_id, "version": data.version}


def get_account(account_id: str, version: str = "v1") -> Optional[dict]:
    """Get account from MongoDB."""
    db = get_db()
    if db is None:
        return None
    return db.accounts.find_one(
        {"account_id": account_id, "version": version},
        {"_id": 0}
    )


def get_memo(account_id: str, version: str = "v1") -> Optional[dict]:
    """Get just the account memo."""
    account = get_account(account_id, version)
    return account.get("account_memo") if account else None


def list_accounts() -> list:
    """List all accounts."""
    db = get_db()
    if db is None:
        return []
    return list(db.accounts.find({}, {
        "_id": 0, "account_id": 1, "version": 1, 
        "company_name": 1, "pipeline_type": 1, "updated_at": 1
    }).sort([("account_id", 1), ("version", 1)]))


def delete_account(account_id: str, version: Optional[str] = None) -> int:
    """Delete account(s)."""
    db = get_db()
    if db is None:
        return 0
    query = {"account_id": account_id}
    if version:
        query["version"] = version
    result = db.accounts.delete_many(query)
    return result.deleted_count

"""
Configuration and Environment Settings
"""
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============ PATHS ============
# Support both local development and Docker container paths

def _get_project_root() -> Path:
    # In Docker, we mount to /app
    if Path("/app/dataset").exists():
        return Path("/app")
    # Local development
    return Path(__file__).parent.parent


PROJECT_ROOT = _get_project_root()
DATASET_DIR = PROJECT_ROOT / "dataset"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "accounts"

# ============ API CONFIGURATION ============

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.1-8b-instant"

# ============ LOGGING ============

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("clara")


def get_groq_api_key() -> str:
    """Get Groq API key with validation."""
    if not GROQ_API_KEY:
        raise ValueError(
            "GROQ_API_KEY not set. Get free key at https://console.groq.com"
        )
    return GROQ_API_KEY


def get_dataset_path(call_type: str) -> Path:
    """Get path to demo or onboarding dataset folder."""
    return DATASET_DIR / call_type


def get_output_path(account_id: str, version: str = "v1") -> Path:
    """Get path to account output folder. Creates if doesn't exist."""
    output_path = OUTPUT_DIR / account_id / version
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path


def get_all_accounts() -> list[str]:
    """Get list of all account IDs with outputs."""
    if not OUTPUT_DIR.exists():
        return []
    return [d.name for d in OUTPUT_DIR.iterdir() if d.is_dir()]

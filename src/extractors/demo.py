"""
PIPELINE A: Demo Call → Preliminary Agent (v1)

Extracts structured account information from demo call transcripts
using LangChain structured output with Pydantic models.
"""
from pathlib import Path
from typing import Any, Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

from src.config import (
    GROQ_MODEL,
    get_dataset_path,
    get_groq_api_key,
    get_output_path,
    logger,
)
from src.schemas import DemoExtraction
from src.utils import (
    extract_account_id_from_filename,
    get_timestamp,
    read_transcript,
    save_json,
)

EXTRACTION_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are a precise data extraction assistant. 
Extract ONLY information explicitly stated in the transcript.
Do NOT guess or make up any information.
If something is not mentioned, leave it as empty string or empty array.
Be precise with phone numbers, addresses, and times.""",
    ),
    (
        "human",
        """Extract business information from this demo call transcript:

{transcript}

Extract all relevant details about the company including:
- Company name
- Business hours (days, start time, end time, timezone)
- Office address
- Services they offer and services they explicitly do NOT offer
- Emergency definitions and contacts
- After hours instructions
- Service area
- Any special instructions or constraints""",
    ),
])


class DemoExtractor:
    """Extract account info from demo call transcripts using LangChain + Groq."""

    def __init__(self):
        api_key = get_groq_api_key()
        self.llm = ChatGroq(
            model=GROQ_MODEL,
            api_key=api_key,
            temperature=0.1,
        ).with_structured_output(DemoExtraction)
        self.chain = EXTRACTION_PROMPT | self.llm

    def extract(self, transcript: str) -> Optional[DemoExtraction]:
        """Extract structured data from transcript using LangChain."""
        try:
            result = self.chain.invoke({"transcript": transcript})
            logger.info(f"Extracted: {result.company_name}")
            return result
        except Exception as e:
            logger.error(f"Extraction error: {e}")
            return None

    def build_memo(self, extracted: DemoExtraction, account_id: str) -> dict[str, Any]:
        """Build structured account memo from extracted Pydantic model."""
        company_name = extracted.company_name or account_id.replace("_", " ").title()

        memo = {
            "account_id": account_id,
            "company_name": company_name,
            "business_hours": extracted.business_hours.model_dump(),
            "office_address": extracted.office_address,
            "services_supported": extracted.services_supported,
            "emergency_definition": extracted.emergency_definition,
            "emergency_routing_rules": {
                "primary_contact": extracted.emergency_primary_contact,
                "primary_contact_name": extracted.emergency_primary_name,
                "fallback_contacts": extracted.emergency_backup_contacts,
                "escalation_order": [],
                "timeout_seconds": extracted.emergency_timeout_seconds,
            },
            "non_emergency_routing_rules": {
                "business_hours_action": "Transfer to main office",
                "after_hours_action": extracted.after_hours_instructions or "Take message",
            },
            "call_transfer_rules": {
                "main_office_number": extracted.main_office_number,
                "timeout_seconds": 30,
                "max_retries": 2,
                "failure_message": "I'll have someone call you back shortly.",
            },
            "integration_constraints": extracted.integration_constraints.copy(),
            "special_instructions": extracted.special_instructions,
            "service_area": extracted.service_area,
            "questions_or_unknowns": [],
            "notes": "",
        }

        # Services NOT offered go into constraints
        for service in extracted.services_not_offered:
            memo["integration_constraints"].append(f"Do not offer: {service}")

        # Build flow summaries
        memo["office_hours_flow_summary"] = self._build_office_hours_flow(memo)
        memo["after_hours_flow_summary"] = self._build_after_hours_flow(memo)

        # Metadata
        memo["version"] = "v1"
        memo["created_at"] = get_timestamp()
        memo["updated_at"] = get_timestamp()

        return memo

    def _build_office_hours_flow(self, memo: dict) -> str:
        """Build business hours call flow summary."""
        main_number = memo["call_transfer_rules"]["main_office_number"] or "main office"
        return (
            f"Greet caller → Identify purpose → Collect name & number → "
            f"Transfer to {main_number} → If transfer fails, take message → "
            f"Confirm callback → Ask 'anything else?' → Close"
        )

    def _build_after_hours_flow(self, memo: dict) -> str:
        """Build after-hours call flow summary."""
        emergency_contact = (
            memo["emergency_routing_rules"]["primary_contact"] or "on-call technician"
        )
        return (
            f"Greet caller → Ask if emergency → If emergency: collect name, number, "
            f"address immediately → Transfer to {emergency_contact} → If transfer fails, "
            f"assure callback within 15 min → If not emergency: take message → "
            f"Confirm next-day callback → Ask 'anything else?' → Close"
        )

    def process_file(self, transcript_path: Path) -> Optional[dict[str, Any]]:
        """Process a single demo transcript file."""
        logger.info(f"Processing: {transcript_path.name}")

        transcript = read_transcript(transcript_path)
        extracted = self.extract(transcript)

        if not extracted:
            logger.error(f"Extraction failed for {transcript_path.name}")
            return None

        account_id = extract_account_id_from_filename(transcript_path.name)
        memo = self.build_memo(extracted, account_id)

        output_path = get_output_path(account_id, "v1")
        save_json(memo, output_path / "account_memo.json")
        save_json(extracted.model_dump(), output_path / "raw_extraction.json")

        logger.info(f"✓ Saved v1 outputs for {account_id}")
        return memo


def process_all_demos(force: bool = False) -> list:
    """Process all demo transcripts in dataset folder.
    
    Args:
        force: If True, reprocess even if output already exists.
    """
    extractor = DemoExtractor()
    demo_path = get_dataset_path("demo")

    if not demo_path.exists():
        logger.error(f"Demo folder not found: {demo_path}")
        return []

    files = list(demo_path.glob("*.txt"))
    logger.info(f"Found {len(files)} demo transcripts")

    results = []
    skipped = 0
    for file_path in files:
        try:
            account_id = extract_account_id_from_filename(file_path.name)
            output_path = get_output_path(account_id, "v1")
            
            # Skip if already processed (unless force=True)
            if not force and (output_path / "account_memo.json").exists():
                logger.info(f"⏭ Skipping {account_id} (v1 already exists)")
                skipped += 1
                continue
            
            memo = extractor.process_file(file_path)
            if memo:
                results.append({"account_id": account_id, **memo})
        except Exception as e:
            logger.error(f"Error processing {file_path.name}: {e}")

    logger.info(f"Processed {len(results)}, skipped {skipped}, total {len(files)} demo calls")
    return results


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("PIPELINE A: Demo Call → Agent v1")
    print("=" * 50 + "\n")

    results = process_all_demos()

    print(f"\n✓ Processed {len(results)} accounts")
    for r in results:
        print(f"  - {r['account_id']}: {r['company_name']}")

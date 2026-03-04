"""
PIPELINE B: Onboarding Call → Agent Update (v1 → v2)

Processes onboarding transcripts to update existing agent configurations
using LangChain structured output with Pydantic models.
"""
import json
from copy import deepcopy
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
from src.schemas import OnboardingExtraction
from src.utils import (
    extract_account_id_from_filename,
    get_timestamp,
    load_json,
    read_transcript,
    save_json,
)

UPDATE_EXTRACTION_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are a precise data extraction assistant.
Find ALL changes, updates, corrections, and additions mentioned in the onboarding call.
ONLY include fields that have actual changes. Leave unchanged fields as null or empty.
Compare against the current configuration to identify what's different.
You MUST respond with valid JSON matching the schema exactly.""",
    ),
    (
        "human",
        """Analyze this onboarding call to find updates to an existing business configuration. Return as JSON.

CURRENT CONFIGURATION:
{current_config}

ONBOARDING TRANSCRIPT:
{transcript}

Extract all changes including:
- Business hours updates (days, start/end times, timezone)
- New services being added
- Services they now DO offer that weren't offered before (removed restrictions)
- Emergency contact changes (numbers, names, backup contacts)
- Office number changes
- Service area updates
- New special instructions
- New constraints (things to never say/do)
- Pricing or promotions
- Callback timeframe changes
- Brief summary of all changes

Return as JSON.""",
    ),
])


class OnboardingProcessor:
    """Process onboarding calls to update existing agent configurations using LangChain."""

    def __init__(self):
        api_key = get_groq_api_key()
        self.llm = ChatGroq(
            model=GROQ_MODEL,
            api_key=api_key,
            temperature=0.1,
        ).with_structured_output(OnboardingExtraction, method="json_mode")
        self.chain = UPDATE_EXTRACTION_PROMPT | self.llm

    def extract_updates(
        self, transcript: str, current_memo: dict
    ) -> Optional[OnboardingExtraction]:
        """Extract updates from onboarding transcript using LangChain."""
        try:
            result = self.chain.invoke({
                "current_config": json.dumps(current_memo, indent=2),
                "transcript": transcript,
            })
            logger.info(f"Extracted updates: {result.changes_summary}")
            return result
        except Exception as e:
            logger.error(f"Update extraction failed: {e}")
            return None

    def apply_updates(
        self, v1_memo: dict, updates: OnboardingExtraction
    ) -> dict[str, Any]:
        """Apply extracted Pydantic updates to create v2 memo."""
        v2_memo = deepcopy(v1_memo)

        # Update business hours
        if updates.business_hours_update:
            hours = updates.business_hours_update
            if hours.days:
                v2_memo["business_hours"]["days"] = hours.days
            if hours.start:
                v2_memo["business_hours"]["start"] = hours.start
            if hours.end:
                v2_memo["business_hours"]["end"] = hours.end
            if hours.timezone:
                v2_memo["business_hours"]["timezone"] = hours.timezone

        # Add new services
        if updates.new_services:
            v2_memo["services_supported"].extend(updates.new_services)

        # Handle removed restrictions
        for item in updates.removed_restrictions:
            constraint = f"Do not offer: {item}"
            if constraint in v2_memo.get("integration_constraints", []):
                v2_memo["integration_constraints"].remove(constraint)
            if item not in v2_memo["services_supported"]:
                v2_memo["services_supported"].append(item)

        # Update emergency contacts
        if updates.emergency_contact_updates:
            emer = updates.emergency_contact_updates
            if emer.primary_contact:
                v2_memo["emergency_routing_rules"]["primary_contact"] = emer.primary_contact
            if emer.primary_name:
                v2_memo["emergency_routing_rules"]["primary_contact_name"] = emer.primary_name
            if emer.backup_contacts:
                v2_memo["emergency_routing_rules"]["fallback_contacts"] = emer.backup_contacts
            if emer.timeout_seconds:
                v2_memo["emergency_routing_rules"]["timeout_seconds"] = emer.timeout_seconds

        # Update office number
        if updates.office_number_update:
            v2_memo["call_transfer_rules"]["main_office_number"] = updates.office_number_update

        # Update service area
        if updates.service_area_update:
            v2_memo["service_area"] = updates.service_area_update

        # Add new instructions
        if updates.new_instructions:
            v2_memo["special_instructions"].extend(updates.new_instructions)

        # Add new constraints
        if updates.new_constraints:
            v2_memo["integration_constraints"].extend(updates.new_constraints)

        # Add pricing info to notes
        if updates.pricing_promotions:
            v2_memo["notes"] += "\nPricing/Promotions: " + "; ".join(updates.pricing_promotions)

        # Update callback timeframe
        if updates.callback_timeframe_update:
            v2_memo["call_transfer_rules"]["failure_message"] = updates.callback_timeframe_update

        # Update metadata
        v2_memo["version"] = "v2"
        v2_memo["updated_at"] = get_timestamp()

        return v2_memo

    def generate_changelog(self, v1: dict, v2: dict, summary: str) -> dict[str, Any]:
        """Generate detailed changelog between v1 and v2."""
        changelog = {
            "account_id": v2["account_id"],
            "company_name": v2["company_name"],
            "transition": "v1 → v2",
            "updated_at": get_timestamp(),
            "summary": summary,
            "changes": [],
        }

        def compare_and_log(v1_val: Any, v2_val: Any, label: str):
            if v1_val != v2_val:
                changelog["changes"].append({
                    "field": label,
                    "old_value": v1_val,
                    "new_value": v2_val,
                })

        # Compare key fields
        compare_and_log(v1.get("business_hours"), v2.get("business_hours"), "Business Hours")
        compare_and_log(v1.get("services_supported"), v2.get("services_supported"), "Services")
        compare_and_log(
            v1.get("emergency_routing_rules"),
            v2.get("emergency_routing_rules"),
            "Emergency Routing",
        )
        compare_and_log(v1.get("service_area"), v2.get("service_area"), "Service Area")
        compare_and_log(
            v1.get("special_instructions"),
            v2.get("special_instructions"),
            "Special Instructions",
        )
        compare_and_log(
            v1.get("integration_constraints"),
            v2.get("integration_constraints"),
            "Integration Constraints",
        )
        compare_and_log(
            v1.get("call_transfer_rules"),
            v2.get("call_transfer_rules"),
            "Call Transfer Rules",
        )

        changelog["total_changes"] = len(changelog["changes"])
        return changelog

    def process_file(self, transcript_path: Path) -> Optional[dict[str, Any]]:
        """Process a single onboarding transcript."""
        logger.info(f"Processing: {transcript_path.name}")

        account_id = extract_account_id_from_filename(transcript_path.name)

        # Load v1 memo
        v1_path = get_output_path(account_id, "v1")
        v1_memo_file = v1_path / "account_memo.json"

        if not v1_memo_file.exists():
            logger.error(f"No v1 memo found for {account_id}. Run demo extraction first.")
            return None

        v1_memo = load_json(v1_memo_file)
        transcript = read_transcript(transcript_path)

        # Extract updates using LangChain
        updates = self.extract_updates(transcript, v1_memo)
        if not updates:
            logger.warning(f"No updates extracted for {account_id}")
            return v1_memo

        # Apply updates to create v2
        v2_memo = self.apply_updates(v1_memo, updates)

        # Generate changelog
        summary = updates.changes_summary or "Onboarding updates applied"
        changelog = self.generate_changelog(v1_memo, v2_memo, summary)

        # Save v2 outputs
        v2_path = get_output_path(account_id, "v2")
        save_json(v2_memo, v2_path / "account_memo.json")
        save_json(changelog, v2_path / "changelog.json")
        save_json(updates.model_dump(), v2_path / "raw_updates.json")

        logger.info(f"✓ Created v2 for {account_id} with {changelog['total_changes']} changes")
        return v2_memo


def process_all_onboarding(force: bool = False) -> list[dict]:
    """Process all onboarding transcripts.
    
    Args:
        force: If True, reprocess even if output already exists.
    """
    processor = OnboardingProcessor()
    onboarding_path = get_dataset_path("onboarding")

    if not onboarding_path.exists():
        logger.error(f"Onboarding folder not found: {onboarding_path}")
        return []

    files = list(onboarding_path.glob("*.txt"))
    logger.info(f"Found {len(files)} onboarding transcripts")

    results = []
    skipped = 0
    for file_path in files:
        try:
            account_id = extract_account_id_from_filename(file_path.name)
            v2_path = get_output_path(account_id, "v2")
            
            # Skip if already processed (unless force=True)
            if not force and (v2_path / "account_memo.json").exists():
                logger.info(f"⏭ Skipping {account_id} (v2 already exists)")
                skipped += 1
                continue
            
            memo = processor.process_file(file_path)
            if memo:
                results.append({"account_id": account_id, **memo})
        except Exception as e:
            logger.error(f"Error processing {file_path.name}: {e}")

    logger.info(f"Processed {len(results)}, skipped {skipped}, total {len(files)} onboarding calls")
    return results


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("PIPELINE B: Onboarding → Agent v2")
    print("=" * 50 + "\n")

    results = process_all_onboarding()

    print(f"\n✓ Updated {len(results)} accounts to v2")
    for r in results:
        print(f"  - {r['account_id']}: {r['company_name']}")

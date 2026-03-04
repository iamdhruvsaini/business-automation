"""
Generate Retell Agent Specifications from Account Memos

Converts structured account memos into Retell-compatible agent configurations
with proper system prompts and call handling protocols.
"""
from pathlib import Path
from typing import Any

from src.config import get_all_accounts, get_output_path, logger
from src.utils import format_business_hours, get_timestamp, load_json, save_json


def generate_system_prompt(memo: dict[str, Any]) -> str:
    """Generate complete system prompt for Retell agent."""

    company = memo.get("company_name", "our company")
    hours = memo.get("business_hours", {})
    hours_str = format_business_hours(hours)
    services = ", ".join(memo.get("services_supported", ["general services"]))
    emergency_def = memo.get("emergency_definition", [])
    emergency_list = ", ".join(emergency_def) if emergency_def else "urgent situations"
    service_area = memo.get("service_area", "our service area")

    # Emergency contacts
    emergency_rules = memo.get("emergency_routing_rules", {})
    primary_contact = emergency_rules.get("primary_contact", "on-call technician")
    fallback = emergency_rules.get("fallback_contacts", [])
    timeout = emergency_rules.get("timeout_seconds", 30)

    # Call transfer
    transfer_rules = memo.get("call_transfer_rules", {})
    main_office = transfer_rules.get("main_office_number", "our office")
    failure_msg = transfer_rules.get(
        "failure_message", "I'll have someone call you back shortly."
    )

    # Special instructions
    constraints = memo.get("integration_constraints", [])
    special = memo.get("special_instructions", [])

    # Build constraints section
    constraint_text = ""
    if constraints:
        constraint_text = "\n\nIMPORTANT RESTRICTIONS:\n" + "\n".join(
            f"- {c}" for c in constraints
        )

    special_text = ""
    if special:
        special_text = "\n\nSPECIAL INSTRUCTIONS:\n" + "\n".join(
            f"- {s}" for s in special
        )

    prompt = f"""You are a professional phone assistant for {company}.

COMPANY INFO:
- Services: {services}
- Business Hours: {hours_str}
- Service Area: {service_area}

═══════════════════════════════════════════════════
DURING BUSINESS HOURS ({hours_str}):
═══════════════════════════════════════════════════

1. GREETING: "Thank you for calling {company}, this is your virtual assistant. How may I help you today?"

2. LISTEN to their request and determine if it's an emergency or routine matter.

3. COLLECT INFO: Ask for their name and callback number.
   - "May I have your name please?"
   - "And what's the best number to reach you?"

4. FOR ROUTINE CALLS:
   - "Let me transfer you to our office now."
   - Transfer to: {main_office}
   - Wait {timeout} seconds for answer

5. IF TRANSFER FAILS:
   - "{failure_msg}"
   - Collect: name, phone, address, and what they need
   - "We'll call you back within [timeframe]"

6. BEFORE CLOSING: "Is there anything else I can help you with today?"

7. CLOSE: "Thank you for calling {company}. Have a great day!"

═══════════════════════════════════════════════════
AFTER BUSINESS HOURS:
═══════════════════════════════════════════════════

1. GREETING: "Thank you for calling {company}. We're currently closed, but I'm here to help."

2. ASK: "Is this an emergency?"

3. EMERGENCY DEFINITION: {emergency_list}

4. FOR EMERGENCIES:
   - "I understand this is urgent. Let me get your information quickly."
   - Collect IMMEDIATELY: name, phone number, address
   - "I'm connecting you to our emergency line now."
   - Transfer to: {primary_contact}
   - Wait {timeout} seconds
   - If no answer, try backup: {', '.join(fallback) if fallback else 'no backup available'}

5. IF EMERGENCY TRANSFER FAILS:
   - "I've recorded your emergency and someone will call you back within 15 minutes."
   - Confirm all contact details
   - Assure them it's flagged as urgent

6. FOR NON-EMERGENCIES:
   - "I'll take a message and have someone call you first thing tomorrow."
   - Collect: name, phone, address if needed, what they need

7. BEFORE CLOSING: "Is there anything else I can help you with?"

8. CLOSE: "Thank you for calling {company}. Someone will follow up with you soon."
{constraint_text}
{special_text}

═══════════════════════════════════════════════════
CRITICAL RULES:
═══════════════════════════════════════════════════
- NEVER mention "function calls", "API", "transfer function" or technical terms
- NEVER ask too many questions - only collect what's needed for routing
- ALWAYS confirm callback timeframe
- ALWAYS be empathetic and professional
- If unsure about something, take a message rather than guessing"""

    return prompt


def generate_agent_spec(memo: dict[str, Any]) -> dict[str, Any]:
    """Generate complete Retell agent specification from memo."""

    company_name = memo.get("company_name", "Unknown Company")
    version = memo.get("version", "v1")

    system_prompt = generate_system_prompt(memo)

    spec = {
        "agent_name": f"{company_name} Assistant",
        "voice_style": "professional_friendly",
        "version": version,
        "generated_at": get_timestamp(),
        "system_prompt": system_prompt,
        "key_variables": {
            "company_name": company_name,
            "timezone": memo.get("business_hours", {}).get("timezone", ""),
            "business_hours": format_business_hours(memo.get("business_hours", {})),
            "office_address": memo.get("office_address", ""),
            "main_phone": memo.get("call_transfer_rules", {}).get("main_office_number", ""),
            "service_area": memo.get("service_area", ""),
        },
        "emergency_config": {
            "emergency_keywords": memo.get("emergency_definition", []),
            "emergency_transfer_number": memo.get("emergency_routing_rules", {}).get(
                "primary_contact", ""
            ),
            "fallback_numbers": memo.get("emergency_routing_rules", {}).get(
                "fallback_contacts", []
            ),
            "transfer_timeout": memo.get("emergency_routing_rules", {}).get(
                "timeout_seconds", 30
            ),
        },
        "call_transfer_protocol": {
            "business_hours_number": memo.get("call_transfer_rules", {}).get(
                "main_office_number", ""
            ),
            "transfer_timeout": memo.get("call_transfer_rules", {}).get("timeout_seconds", 30),
            "max_retries": memo.get("call_transfer_rules", {}).get("max_retries", 2),
            "failure_script": memo.get("call_transfer_rules", {}).get("failure_message", ""),
        },
        "retell_settings": {
            "voice_provider": "elevenlabs",
            "voice_id": "professional_male",
            "language": "en-US",
            "response_speed": 1.0,
            "interruption_sensitivity": 0.5,
            "ambient_sound": "office",
        },
    }

    return spec


def save_manual_import_guide(spec: dict, output_path: Path):
    """Save human-readable import instructions for Retell UI."""

    guide = f"""# Retell Agent Import Guide
## {spec["agent_name"]} ({spec["version"]})

Generated: {spec["generated_at"]}

---

## Step 1: Create New Agent in Retell

1. Log into https://app.retellai.com
2. Click "Create Agent"
3. Name: `{spec["agent_name"]}`

---

## Step 2: Configure Voice Settings

- Voice Provider: {spec["retell_settings"]["voice_provider"]}
- Language: {spec["retell_settings"]["language"]}
- Response Speed: {spec["retell_settings"]["response_speed"]}

---

## Step 3: Paste System Prompt

Copy everything between the START and END markers below:

```
--- START SYSTEM PROMPT ---
{spec["system_prompt"]}
--- END SYSTEM PROMPT ---
```

---

## Step 4: Configure Phone Integration

- Main Transfer Number: {spec["call_transfer_protocol"]["business_hours_number"]}
- Emergency Number: {spec["emergency_config"]["emergency_transfer_number"]}
- Transfer Timeout: {spec["call_transfer_protocol"]["transfer_timeout"]} seconds

---

## Step 5: Test the Agent

Test scenarios:
1. Business hours routine call
2. Business hours transfer failure
3. After hours non-emergency
4. After hours emergency
5. Emergency transfer failure

---

## Key Variables Reference

| Variable | Value |
|----------|-------|
| Company Name | {spec["key_variables"]["company_name"]} |
| Business Hours | {spec["key_variables"]["business_hours"]} |
| Timezone | {spec["key_variables"]["timezone"]} |
| Service Area | {spec["key_variables"]["service_area"]} |
"""

    with open(output_path / "RETELL_IMPORT_GUIDE.md", "w", encoding="utf-8") as f:
        f.write(guide)

    logger.info(f"Saved: {output_path / 'RETELL_IMPORT_GUIDE.md'}")


def generate_for_account(account_id: str, version: str = "v1") -> dict[str, Any]:
    """Generate agent spec for a specific account version."""
    logger.info(f"Generating agent spec: {account_id}/{version}")

    account_path = get_output_path(account_id, version)
    memo_file = account_path / "account_memo.json"

    if not memo_file.exists():
        logger.error(f"No memo found: {memo_file}")
        return {}

    memo = load_json(memo_file)
    spec = generate_agent_spec(memo)

    save_json(spec, account_path / "retell_agent_spec.json")
    save_manual_import_guide(spec, account_path)

    logger.info(f"✓ Generated agent spec for {account_id}/{version}")
    return spec


def generate_all_specs() -> list[dict]:
    """Generate agent specs for all accounts and versions."""
    accounts = get_all_accounts()

    if not accounts:
        logger.warning("No accounts found. Run demo extraction first.")
        return []

    results = []
    for account_id in accounts:
        # Generate v1 if exists
        v1_path = get_output_path(account_id, "v1")
        if (v1_path / "account_memo.json").exists():
            spec = generate_for_account(account_id, "v1")
            if spec:
                results.append(spec)

        # Generate v2 if exists
        v2_path = get_output_path(account_id, "v2")
        if (v2_path / "account_memo.json").exists():
            spec = generate_for_account(account_id, "v2")
            if spec:
                results.append(spec)

    logger.info(f"Generated {len(results)} agent specs total")
    return results


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("Retell Agent Spec Generator")
    print("=" * 50 + "\n")

    results = generate_all_specs()

    print(f"\n✓ Generated {len(results)} agent specifications")
    for r in results:
        print(f"  - {r['agent_name']} ({r['version']})")

"""
Pydantic Schemas for Structured Output Extraction
Using LangChain's structured output feature for reliable data extraction.
"""
from typing import Optional
from pydantic import BaseModel, Field


# ============ DEMO CALL EXTRACTION SCHEMA ============


class BusinessHours(BaseModel):
    """Business operating hours."""

    days: list[str] = Field(
        default_factory=list,
        description="Days of operation e.g. ['Monday', 'Tuesday']",
    )
    start: str = Field(default="", description="Opening time e.g. '8:00 AM'")
    end: str = Field(default="", description="Closing time e.g. '6:00 PM'")
    timezone: str = Field(default="", description="Timezone e.g. 'EST', 'PST', 'CST'")


class DemoExtraction(BaseModel):
    """Structured data extracted from demo call transcript."""

    company_name: str = Field(description="Exact company name mentioned in the call")

    business_hours: BusinessHours = Field(
        default_factory=BusinessHours, description="Business operating hours"
    )

    office_address: str = Field(default="", description="Full office address if mentioned")

    services_supported: list[str] = Field(
        default_factory=list, description="List of services the company offers"
    )

    services_not_offered: list[str] = Field(
        default_factory=list, description="Services they explicitly do NOT offer"
    )

    emergency_definition: list[str] = Field(
        default_factory=list, description="What situations they consider emergencies"
    )

    emergency_primary_contact: str = Field(
        default="", description="Primary phone number for emergencies"
    )

    emergency_primary_name: str = Field(
        default="", description="Name of primary emergency contact person"
    )

    emergency_backup_contacts: list[str] = Field(
        default_factory=list, description="Backup phone numbers for emergencies"
    )

    emergency_timeout_seconds: int = Field(
        default=30, description="How long to wait before trying backup contact"
    )

    main_office_number: str = Field(
        default="", description="Main office phone number for transfers"
    )

    non_emergency_after_hours_action: str = Field(
        default="Take a message",
        description="Simple string: what to do for NON-EMERGENCY calls after hours. Must be a plain text string like 'Take a message with name and number' - NOT an object.",
    )

    service_area: str = Field(default="", description="Geographic area served")

    special_instructions: list[str] = Field(
        default_factory=list, description="Any special handling instructions mentioned"
    )

    integration_constraints: list[str] = Field(
        default_factory=list,
        description="Things to never say or do (e.g., don't mention software names)",
    )


# ============ ONBOARDING CALL EXTRACTION SCHEMA ============


class BusinessHoursUpdate(BaseModel):
    """Updates to business hours from onboarding."""

    days: Optional[list[str]] = Field(default=None, description="Updated days if changed")
    start: Optional[str] = Field(default=None, description="Updated start time if changed")
    end: Optional[str] = Field(default=None, description="Updated end time if changed")
    timezone: Optional[str] = Field(default=None, description="Updated timezone if changed")


class EmergencyContactUpdate(BaseModel):
    """Updates to emergency contacts from onboarding."""

    primary_contact: Optional[str] = Field(
        default=None, description="New primary number if changed"
    )
    primary_name: Optional[str] = Field(
        default=None, description="New primary contact name if changed"
    )
    backup_contacts: Optional[list[str]] = Field(
        default=None, description="New backup numbers if changed"
    )
    timeout_seconds: Optional[int] = Field(
        default=None, description="New timeout if changed"
    )


class OnboardingExtraction(BaseModel):
    """Updates extracted from onboarding call transcript."""

    business_hours_update: Optional[BusinessHoursUpdate] = Field(
        default=None, description="Changes to business hours"
    )

    new_services: list[str] = Field(
        default_factory=list, description="New services being added"
    )

    removed_restrictions: list[str] = Field(
        default_factory=list,
        description="Services they NOW offer that they didn't before",
    )

    emergency_contact_updates: Optional[EmergencyContactUpdate] = Field(
        default=None, description="Changes to emergency contacts"
    )

    office_number_update: Optional[str] = Field(
        default=None, description="New office number if changed"
    )

    service_area_update: Optional[str] = Field(
        default=None, description="Updated service area description"
    )

    new_instructions: list[str] = Field(
        default_factory=list, description="New special instructions to add"
    )

    new_constraints: list[str] = Field(
        default_factory=list, description="New things to never say/do"
    )

    pricing_promotions: list[str] = Field(
        default_factory=list, description="Any pricing or promotions mentioned"
    )

    callback_timeframe_update: Optional[str] = Field(
        default=None, description="Updated callback promise if mentioned"
    )

    changes_summary: str = Field(
        default="",
        description="Brief summary of all changes from this onboarding call",
    )

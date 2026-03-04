"""
Extractors Package
==================
LLM-powered extraction from call transcripts.
"""
from src.extractors.demo import DemoExtractor, process_all_demos
from src.extractors.onboarding import OnboardingProcessor, process_all_onboarding

__all__ = [
    "DemoExtractor",
    "OnboardingProcessor",
    "process_all_demos",
    "process_all_onboarding",
]

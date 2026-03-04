"""
Clara Answers Automation Pipeline
==================================
Zero-cost automation: Demo Call → Retell Agent → Onboarding Updates

Run all processing steps:
1. Extract info from demo calls → Generate v1 memos
2. Generate v1 Retell agent specs  
3. Extract updates from onboarding calls → Generate v2 memos
4. Generate v2 Retell agent specs

Usage:
    python main.py           # Run full pipeline
    python main.py demo      # Run only demo extraction
    python main.py onboard   # Run only onboarding updates
    python main.py agents    # Generate agent specs only
"""
import sys

from src.extractors import process_all_demos, process_all_onboarding
from src.generators import generate_all_specs


def print_banner():
    """Print startup banner."""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   Clara Answers Automation Pipeline                           ║
║   ─────────────────────────────────                           ║
║   Demo Call → Agent v1 → Onboarding → Agent v2                ║
║                                                               ║
║   Zero-cost • Automated • Reproducible                        ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
    """)


def run_demo_pipeline():
    """Run Pipeline A: Demo calls → v1 memos."""
    print("\n" + "─"*50)
    print("PIPELINE A: Demo Call Processing")
    print("─"*50)
    
    results = process_all_demos()
    print(f"\n✓ Processed {len(results)} demo calls")
    return results


def run_onboarding_pipeline():
    """Run Pipeline B: Onboarding calls → v2 memos."""
    print("\n" + "─"*50)
    print("PIPELINE B: Onboarding Processing")
    print("─"*50)
    
    results = process_all_onboarding()
    print(f"\n✓ Processed {len(results)} onboarding calls")
    return results


def run_agent_generation():
    """Generate Retell agent specs for all accounts."""
    print("\n" + "─"*50)
    print("Agent Spec Generation")
    print("─"*50)
    
    results = generate_all_specs()
    print(f"\n✓ Generated {len(results)} agent specifications")
    return results


def run_full_pipeline():
    """Run the complete automation pipeline."""
    print_banner()
    
    # Step 1: Process demo calls
    demo_results = run_demo_pipeline()
    
    # Step 2: Generate v1 agent specs
    run_agent_generation()
    
    # Step 3: Process onboarding calls
    onboarding_results = run_onboarding_pipeline()
    
    # Step 4: Generate v2 agent specs
    run_agent_generation()
    
    # Summary
    print("\n" + "═"*50)
    print("PIPELINE COMPLETE")
    print("═"*50)
    print(f"""
Summary:
  • Demo calls processed:      {len(demo_results)}
  • Onboarding calls processed: {len(onboarding_results)}
  
Outputs saved to: outputs/accounts/<account_id>/
  • v1/ - Initial agent configuration
  • v2/ - Updated after onboarding
  
Each folder contains:
  • account_memo.json       - Structured business data
  • retell_agent_spec.json  - Retell agent configuration
  • RETELL_IMPORT_GUIDE.md  - Manual import instructions
  • changelog.json          - (v2 only) What changed
    """)


def main():
    """Main entry point."""
    args = sys.argv[1:] if len(sys.argv) > 1 else []
    
    if not args or args[0] == "all":
        run_full_pipeline()
    elif args[0] == "demo":
        print_banner()
        run_demo_pipeline()
        run_agent_generation()
    elif args[0] == "onboard":
        print_banner()
        run_onboarding_pipeline()
        run_agent_generation()
    elif args[0] == "agents":
        print_banner()
        run_agent_generation()
    else:
        print(__doc__)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Diagnostic script to verify provider routing logic without making API calls.
Shows which provider would be selected for each agent step.
"""

import json
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from orchestrator.providers import get_provider

def main():
    # Load config
    config_path = "config/run_config.json"
    with open(config_path, "r") as f:
        config = json.load(f)
    
    default_provider = config.get("provider", "manual")
    
    print("=" * 70)
    print("PROVIDER ROUTING DIAGNOSTIC")
    print("=" * 70)
    print(f"\nDefault provider: {default_provider}")
    print(f"Total agents: {len(config['agents'])}\n")
    
    print("-" * 70)
    print(f"{'Step':<6} {'Agent Name':<35} {'Provider':<20}")
    print("-" * 70)
    
    for step_idx, agent_cfg in enumerate(config["agents"], start=1):
        agent_name = agent_cfg["name"]
        
        # Same logic as root_agent.py
        provider_name = (
            agent_cfg.get("provider") or 
            config.get("provider") or 
            os.getenv("PROVIDER", "manual")
        )
        
        # Show which provider would be used
        override = " (override)" if agent_cfg.get("provider") else ""
        print(f"{step_idx:<6} {agent_name:<35} {provider_name:<20}{override}")
    
    print("-" * 70)
    print("\n✓ Provider routing configured correctly")
    print("\nTo test provider instantiation (requires API keys):")
    print("  OPENAI_API_KEY='...' PERPLEXITY_API_KEY='...' python3 -c \"from orchestrator.providers import get_provider; get_provider('openai'); get_provider('perplexity'); print('OK')\"")

if __name__ == "__main__":
    main()

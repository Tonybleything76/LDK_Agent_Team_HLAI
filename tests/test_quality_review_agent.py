import pytest
import json
from pathlib import Path

from orchestrator.agents.quality_review_agent import run_quality_review
from orchestrator.providers.dry_run_provider import DryRunProvider

def test_quality_review_agent_json_contract_and_score():
    """Test 1 & 2: JSON contract integrity and Score between 0-10."""
    sb_state = {"mock": "state"}
    la_state = {"mock": "la"}
    
    # We use dry_run provider
    report = run_quality_review(
        storyboard_state=sb_state,
        la_state=la_state,
        provider_name="dry_run"
    )
    
    # Contract
    assert "quality_score" in report
    assert "premium_flag" in report
    assert "domain_scores" in report
    assert "observations" in report
    assert "improvement_recommendations" in report
    
    # Score bounds
    assert 0 <= report["quality_score"] <= 10
    for k, v in report["domain_scores"].items():
        assert 0 <= v <= 2

def test_quality_review_agent_premium_flag():
    """Test 3: Premium flag logic."""
    sb_state = {"content": "excellent governance reflection"}
    la_state = {"content": "mock"}
    
    report = run_quality_review(
        storyboard_state=sb_state,
        la_state=la_state,
        provider_name="dry_run"
    )
    
    assert report["premium_flag"] is True

def test_quality_review_missing_governance():
    """Test 4: Missing governance model lowers score."""
    # Omit governance and reflection 
    sb_state = {"content": "plain text without gov or ref"}
    la_state = {"content": "mock"}
    
    report = run_quality_review(
        storyboard_state=sb_state,
        la_state=la_state,
        provider_name="dry_run"
    )
    
    assert report["domain_scores"]["governance_anchor"] == 0
    assert report["quality_score"] < 10

def test_quality_review_missing_reflection():
    """Test 5: Missing reflection lowers dialogue score."""
    sb_state = {"content": "governance is here but no refl"}
    la_state = {"content": "mock"}
    
    report = run_quality_review(
        storyboard_state=sb_state,
        la_state=la_state,
        provider_name="dry_run"
    )
    
    assert report["domain_scores"]["dialogue_density"] == 0
    assert report["quality_score"] < 10


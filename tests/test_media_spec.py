import pytest
import json
from datetime import datetime
from orchestrator.media_spec import validate_media_spec, verify_integrity
from orchestrator.course_architecture import stable_hash

# Fixtures for testing

@pytest.fixture
def sample_architecture():
    return {
        "course_id": "course_123",
        "version": "0.6.0",
        "generated_at_utc": "2023-01-01T00:00:00Z",
        "scenario_anchors": [
            {
                "id": "scn_1", 
                "title": "T1", 
                "description": "D1", 
                "source_ref": "ref1"
            },
            {
                "id": "scn_2", 
                "title": "T2", 
                "description": "D2", 
                "source_ref": "ref2"
            }
        ],
        "learning_objects": []
    }

@pytest.fixture
def sample_media_spec(sample_architecture):
    arch_hash = stable_hash(sample_architecture)
    return {
        "course_id": "course_123",
        "architecture_hash": arch_hash,
        "generated_at_utc": datetime.utcnow().isoformat() + "Z",
        "media_assets": [
            {
                "learning_object_id": "lo_1",
                "slides": [
                    {
                        "order": 1,
                        "layout": "title",
                        "title": "Welcome",
                        "narration": "Hello world",
                        "duration_seconds": 10
                    }
                ]
            }
        ]
    }

def test_validate_valid_spec(sample_media_spec):
    """Test that a valid spec passes validation."""
    validate_media_spec(sample_media_spec)

def test_validate_missing_field(sample_media_spec):
    """Test that missing required fields raises ValueError."""
    del sample_media_spec["architecture_hash"]
    with pytest.raises(ValueError, match="Validation failed"):
        validate_media_spec(sample_media_spec)

def test_validate_invalid_layout(sample_media_spec):
    """Test that invalid enum values raise ValueError."""
    sample_media_spec["media_assets"][0]["slides"][0]["layout"] = "invalid_layout_type"
    with pytest.raises(ValueError, match="Validation failed"):
        validate_media_spec(sample_media_spec)

def test_integrity_check_success(sample_media_spec, sample_architecture):
    """Test that matching hash and ID passes integrity check."""
    assert verify_integrity(sample_media_spec, sample_architecture) is True

def test_integrity_check_mismatch_id(sample_media_spec, sample_architecture):
    """Test that mismatched course_id raises error."""
    sample_media_spec["course_id"] = "course_999"
    with pytest.raises(ValueError, match="Course ID mismatch"):
        verify_integrity(sample_media_spec, sample_architecture)

def test_integrity_check_mismatch_hash(sample_media_spec, sample_architecture):
    """Test that mismatched hash raises error."""
    # Modify architecture so hash changes
    sample_architecture["version"] = "0.6.1"
    
    with pytest.raises(ValueError, match="Integrity Error"):
        verify_integrity(sample_media_spec, sample_architecture)

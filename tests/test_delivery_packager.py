import pytest
import shutil
from pathlib import Path
from services.delivery_packager import DeliveryPackager

@pytest.fixture
def clean_dist_dir(tmp_path):
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    yield output_dir

def test_delivery_packager(clean_dist_dir):
    packager = DeliveryPackager(clean_dist_dir)
    
    media_spec = {
        "course_id": "test_course",
        "media_assets": [
            {
                "learning_object_id": "lo_1",
                "slides": [
                    {
                        "order": 1,
                        "layout": "title",
                        "title": "Welcome",
                        "narration": "Hello"
                    }
                ]
            }
        ]
    }
    
    results = packager.process(media_spec)
    
    # Check return values
    assert "slides_html" in results
    assert "scorm_zip" in results
    
    # Check file existence
    assert Path(results["slides_html"]).exists()
    assert Path(results["scorm_zip"]).exists()
    
    # Check generated slide content
    with open(results["slides_html"], "r") as f:
        content = f.read()
        assert "Welcome" in content
        assert "slide-layout-title" in content

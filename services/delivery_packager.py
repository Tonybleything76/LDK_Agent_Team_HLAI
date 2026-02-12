"""
Delivery Packager Service

Converts `media_spec.json` into deployable artifacts:
1. Slide Bundle (Reveal.js stub / HTML)
2. SCORM Package (stub)
"""

import json
import os
import shutil
from pathlib import Path
from typing import Dict, Any

class DeliveryPackager:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.dist_dir = output_dir / "dist"
        self.dist_dir.mkdir(parents=True, exist_ok=True)

    def process(self, media_spec: Dict[str, Any]) -> Dict[str, str]:
        """
        Run all packaging tasks.
        
        Args:
            media_spec: Validated media specification
            
        Returns:
            Dict of generated file paths
        """
        results = {}
        
        # 1. Generate Slides
        slide_path = self._generate_slides(media_spec)
        results["slides_html"] = str(slide_path)
        
        # 2. Generate SCORM
        scorm_path = self._generate_scorm_package(media_spec)
        results["scorm_zip"] = str(scorm_path)
        
        return results

    def _generate_slides(self, media_spec: Dict[str, Any]) -> Path:
        """Generate a single HTML file with Reveal.js structure."""
        course_id = media_spec.get("course_id", "course")
        outfile = self.dist_dir / f"{course_id}_presentation.html"
        
        # Basic HTML Template
        html_content = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            f"<title>{course_id} Presentation</title>",
            "<style>",
            "  body { font-family: sans-serif; background: #f0f0f0; }",
            "  .slide { background: white; padding: 40px; margin: 20px auto; max-width: 800px; border: 1px solid #ccc; }",
            "  .slide-title { font-size: 2em; margin-bottom: 0.5em; }",
            "  .slide-layout-title { text-align: center; color: #333; }",
            "  .narr { color: #666; font-style: italic; margin-top: 20px; border-top: 1px solid #eee; padding-top: 10px; }",
            "</style>",
            "</head>",
            "<body>"
        ]
        
        assets = media_spec.get("media_assets", [])
        for item in assets:
            lo_id = item.get("learning_object_id")
            slides = item.get("slides", [])
            
            html_content.append(f"<!-- Learning Object: {lo_id} -->")
            
            for slide in slides:
                layout = slide.get("layout", "bullet_list")
                title = slide.get("title", "")
                bullets = slide.get("bullets", [])
                narration = slide.get("narration", "")
                visual = slide.get("visual_prompt", "")
                
                html_content.append(f'<div class="slide slide-layout-{layout}">')
                html_content.append(f'<div class="slide-title">{title}</div>')
                
                if bullets:
                    html_content.append("<ul>")
                    for b in bullets:
                        html_content.append(f"<li>{b}</li>")
                    html_content.append("</ul>")
                    
                if visual:
                    html_content.append(f'<div class="visual">[Image: {visual}]</div>')
                    
                html_content.append(f'<div class="narr">Spec Narration: {narration}</div>')
                html_content.append("</div>")
                
        html_content.append("</body></html>")
        
        with open(outfile, "w") as f:
            f.write("\n".join(html_content))
            
        return outfile

    def _generate_scorm_package(self, media_spec: Dict[str, Any]) -> Path:
        """Create a zip file with imsmanifest.xml stub."""
        course_id = media_spec.get("course_id", "course")
        pkg_dir = self.dist_dir / f"{course_id}_scorm"
        pkg_dir.mkdir(parents=True, exist_ok=True)
        
        # Create manifest
        manifest_content = f"""<?xml version="1.0" standalone="no" ?>
<manifest identifier="{course_id}" version="1.0">
  <metadata>
    <schema>ADL SCORM</schema>
    <schemaversion>1.2</schemaversion>
  </metadata>
  <organizations default="org_1">
    <organization identifier="org_1">
      <title>Course {course_id}</title>
      <item identifier="item_1" identifierref="resource_1">
        <title>Main Content</title>
      </item>
    </organization>
  </organizations>
  <resources>
    <resource identifier="resource_1" type="webcontent" href="index.html">
      <file href="index.html"/>
    </resource>
  </resources>
</manifest>
"""
        with open(pkg_dir / "imsmanifest.xml", "w") as f:
            f.write(manifest_content)
            
        # Create dummy content
        with open(pkg_dir / "index.html", "w") as f:
            f.write("<html><body><h1>SCORM Content Placeholder</h1></body></html>")
            
        # Zip it
        zip_path = self.dist_dir / f"{course_id}_scorm_package"
        shutil.make_archive(str(zip_path), 'zip', pkg_dir)
        
        # Cleanup dir
        shutil.rmtree(pkg_dir)
        
        return Path(f"{str(zip_path)}.zip")

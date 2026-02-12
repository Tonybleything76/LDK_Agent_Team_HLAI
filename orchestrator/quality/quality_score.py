import os
import json
import re
from pathlib import Path
from typing import Dict, Any

def calculate_quality_score(run_dir: str) -> Dict[str, Any]:
    """
    Calculates a deterministic quality score (0-100) for the run based on text artifacts.
    
    Scoring Dimensions:
    1. Scenario Density (30pts)
       - Based on count of [Scenario: ...] tags across all agent outputs.
    2. SME Nuance Presence (30pts) 
       - Based on presence of vocabulary from SME notes (simple keyword overlap).
    3. Structural Completeness (20pts)
       - Checks for key sections like "Learning Objectives", "Practice", "Assessment".
    4. Anti-Genericism (20pts)
       - Penalizes use of "banned" generic AI phrases.
       
    Returns:
        Dict containing total score and breakdown.
    """
    
    score_breakdown = {
        "scenario_density": 0,
        "sme_nuance": 0,
        "structural_completeness": 0,
        "anti_genericism": 0
    }
    
    # 1. Gather all markdown content from the run
    # We focus on instructional agents
    target_agents = [
        "instructional_designer_agent", 
        "storyboard_agent",
        "assessment_designer_agent"
    ]
    
    files = sorted(Path(run_dir).glob("*.md"))
    combined_content = ""
    
    for f in files:
        # Simple check if file belongs to a target agent
        if any(agent in f.name for agent in target_agents):
            try:
                combined_content += f.read_text(encoding="utf-8") + "\n"
            except:
                pass
                
    if not combined_content:
        return {
            "total_score": 0,
            "grade": "F",
            "breakdown": score_breakdown,
            "message": "No instructional content found to score."
        }

    # --- Dimension 1: Scenario Density (Max 30) ---
    # 2 pts per scenario citation, capped at 30 (15 citations total across course)
    anchor_pattern = r"\[Scenario:\s*[^\]]+\]"
    anchors = re.findall(anchor_pattern, combined_content, re.IGNORECASE)
    score_breakdown["scenario_density"] = min(30, len(anchors) * 2)

    # --- Dimension 2: SME Nuance (Max 30) ---
    # Heuristic: Check for specific terms from the inputs/sme_notes.md if available
    # For now, we'll verify if we can find inputs.
    # Since we don't have easy access to inputs content here without IO, we will rely on 
    # checking for the "sme_nuances" field in the course_architecture.json if present
    # OR just look for quoted terms.
    
    # Let's try to load course_architecture.json from the run_dir to get nuance terms
    ca_path = Path(run_dir) / "course_architecture.json"
    nuance_score = 0
    
    if ca_path.exists():
        try:
            with open(ca_path, 'r') as f:
                ca = json.load(f)
            
            # Extract nuances from LOs
            nuances = []
            if "learning_objects" in ca:
                for lo in ca["learning_objects"]:
                    # We accept 'sme_nuances' (new schema)
                    if "sme_nuances" in lo:
                        nuances.extend(lo["sme_nuances"])
            
            # Simple keyword matching
            hits = 0
            for term in nuances:
                # Naive matching of terms > 4 chars
                if len(term) > 4 and term.lower() in combined_content.lower():
                    hits += 1
            
            # 5 pts per unique nuance used, capped at 30
            nuance_score = min(30, hits * 5)
            
        except Exception:
            nuance_score = 0
            
    # Fallback if no CA or parse error: give partial credit if "Nuance" word appears? No, be strict.
    score_breakdown["sme_nuance"] = nuance_score

    # --- Dimension 3: Structural Completeness (Max 20) ---
    required_sections = [
        "Learning Objectives",
        "Key Decisions", # Custom for this pilot
        "Common Pitfalls",
        "Assessment",
        "Practice",
        "Feedback"
    ]
    
    sections_found = 0
    for sec in required_sections:
        if re.search(f"#+.*{sec}", combined_content, re.IGNORECASE):
            sections_found += 1
            
    # Scale to 20
    score_breakdown["structural_completeness"] = int((sections_found / len(required_sections)) * 20)

    # --- Dimension 4: Anti-Genericism (Max 20) ---
    # Start at 20, deduct for banned phrases
    # Words to penalize:
    banned = [
        "tapestry", "game-changer", "landscape", "delve", "explore the world of",
        "In this module, we will", "It is important to note", "Remember that",
        "In conclusion", "realm of", "testament to"
    ]
    
    penalty = 0
    for phrase in banned:
        count = combined_content.lower().count(phrase.lower())
        penalty += count * 2 # 2 pts penalty per occurrence
        
    score_breakdown["anti_genericism"] = max(0, 20 - penalty)
    
    # --- Total ---
    total = sum(score_breakdown.values())
    
    grade = "F"
    if total >= 90: grade = "A"
    elif total >= 80: grade = "B"
    elif total >= 70: grade = "C"
    elif total >= 60: grade = "D"
    
    result = {
        "total_score": total,
        "grade": grade,
        "breakdown": score_breakdown
    }
    
    # Write to file
    with open(os.path.join(run_dir, "quality_score.json"), "w") as f:
        json.dump(result, f, indent=2)
        
    return result

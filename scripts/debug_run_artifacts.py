#!/usr/bin/env python3
import sys
import os
import glob
import json
import re

def load_json(path):
    if not path or not os.path.exists(path):
        return None
    with open(path, 'r') as f:
        return json.load(f)

def get_file_by_pattern(run_dir, pattern):
    files = glob.glob(os.path.join(run_dir, pattern))
    if files:
        return files[0]
    return None

def extract_strings(obj):
    if isinstance(obj, dict):
        return " ".join(extract_strings(v) for v in obj.values())
    elif isinstance(obj, list):
        return " ".join(extract_strings(v) for v in obj)
    elif isinstance(obj, str):
        return obj
    return ""

def get_sentences(text):
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]

def evaluate_alt_text(alt_text, media_desc):
    if not alt_text:
        return False
    stop_words = {"a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for", "with", "of", "is", "are"}
    alt_words = set(re.findall(r'\w+', alt_text.lower())) - stop_words
    desc_words = set(re.findall(r'\w+', (media_desc or "").lower())) - stop_words
    overlap = alt_words.intersection(desc_words)
    return len(overlap) >= 2

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/debug_run_artifacts.py outputs/<run_id>")
        sys.exit(1)

    run_dir = sys.argv[1]
    if not os.path.isdir(run_dir):
        print(f"Directory not found: {run_dir}")
        sys.exit(1)

    la_file = get_file_by_pattern(run_dir, "03_learning_architect_agent_state.json")
    sb_file = get_file_by_pattern(run_dir, "06_storyboard_agent_state.json")
    scripts_file = get_file_by_pattern(run_dir, "*script*state*.json")
    if not scripts_file:
        scripts_file = get_file_by_pattern(run_dir, "04_instructional_designer_agent_state.json")
    assessment_file = get_file_by_pattern(run_dir, "*assessment*state*.json")
    
    la_state = load_json(la_file) or {}
    sb_state = load_json(sb_file) or {}
    sc_state = load_json(scripts_file) or {}
    as_state = load_json(assessment_file) or {}

    print("=======================================")
    print("SECTION 1: ASSESSMENT COVERAGE")
    print("=======================================")
    
    objectives_by_module = {}
    la_updated = la_state.get("updated_state", {})
    curriculum = la_updated.get("curriculum", {})
    modules = curriculum.get("modules", [])
    
    if not modules and "modules" in la_updated:
        modules = la_updated["modules"]

    for m in modules:
        mod_id = m.get("module_id", "Unknown")
        objs = m.get("objectives", [])
        objectives_by_module[mod_id] = objs

    objective_to_questions = {}
    as_updated = as_state.get("updated_state", {})
    assessment = as_updated.get("assessment", {})
    questions = assessment.get("questions", [])
    
    if not questions and "questions" in as_updated:
        questions = as_updated["questions"]

    for q in questions:
        obj_ref = q.get("objective_ref", "")
        q_id = q.get("q_id", q.get("id", "Unknown"))
        if obj_ref not in objective_to_questions:
            objective_to_questions[obj_ref] = []
        objective_to_questions[obj_ref].append(str(q_id))

    for mod_id, objs in objectives_by_module.items():
        print(f"\nModule: {mod_id}")
        for obj in objs:
            mapped = objective_to_questions.get(obj, [])
            if mapped:
                print(f"  [OK] Objective: {obj}\n       -> Mapped Questions: {', '.join(mapped)}")
            else:
                print(f"  [FLAG] Objective: {obj}\n       -> Mapped Questions: NONE (Zero mapped questions)")

    print("\n=======================================")
    print("SECTION 2: STORYBOARD ALT TEXT")
    print("=======================================")
    
    sb_updated = sb_state.get("updated_state", {})
    storyboards = sb_updated.get("storyboards", [])
    if not storyboards and "modules" in sb_updated:
        storyboards = sb_updated.get("modules", [])

    for item in storyboards:
        mod_id = item.get("module_id", "Unknown")
        scenes = item.get("scenes", [item])
        for scene in scenes:
            alt_text = scene.get("alt_text", "")
            media_desc = scene.get("media_asset_description", "")
            
            words = [w for w in alt_text.split() if w.strip()]
            word_count = len(words)
            has_elements = evaluate_alt_text(alt_text, media_desc)
            
            flag_msg = ""
            if not alt_text:
                flag_msg = " [FLAG MISSING]"
            elif word_count < 18:
                flag_msg = " [FLAG < 18 WORDS]"
                
            print(f"Module {mod_id}: {word_count} words.{flag_msg} Contains 2+ concrete elements: {has_elements}")
            if flag_msg:
                print(f"  Alt-text: {alt_text}")

    print("\n=======================================")
    print("SECTION 3: SCRIPT RISK PHRASES")
    print("=======================================")
    
    value_claims = ["value", "roi", "saves time", "increases revenue", "reduces cost", "boosts", "impact"]
    decision_claims = ["ai decides", "ai determines", "let ai decide", "ai chooses", "ai makes the decision"]
    
    sc_updated = sc_state.get("updated_state", {})
    scripts = sc_updated.get("scripts", [])
    
    if not scripts and "modules" in sc_updated:
        scripts = sc_updated["modules"]
    
    if not scripts:
        print("No scripts found in state file.")
        
    for script in scripts:
        mod_id = script.get("module_id", "Unknown")
        text = extract_strings(script)
        sentences = get_sentences(text)
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            
            has_value = any(claim in sentence_lower for claim in value_claims)
            has_decision = any(claim in sentence_lower for claim in decision_claims)
            
            if has_value:
                print(f"Module {mod_id} [needs SME citation]: {sentence}")
            elif has_decision:
                print(f"Module {mod_id} [rewrite to neutral capability]: {sentence}")

if __name__ == '__main__':
    main()

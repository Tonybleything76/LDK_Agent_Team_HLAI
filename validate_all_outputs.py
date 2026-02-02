import json
import sys
from pathlib import Path

# Add the project root to sys.path to allow importing from orchestrator
sys.path.append(str(Path(__file__).parent))

from orchestrator.validation import validate_agent_output_dict

def validate_all(outputs_dir):
    outputs_path = Path(outputs_dir)
    if not outputs_path.exists():
        print(f"Error: Directory {outputs_dir} does not exist.")
        return

    # Group files by agent
    agents = {}
    for item in outputs_path.iterdir():
        if item.is_file():
            # unexpected files might be there, like .DS_Store
            if item.name.startswith('.'):
                continue
            
            # extract agent name from filename
            # format: <id>_<name>.<ext> or <id>_<name>_<suffix>.<ext>
            parts = item.stem.split('_')
            # Assuming format: 01_strategy_lead_agent...
            if len(parts) >= 2 and parts[0].isdigit():
                agent_id = parts[0]
                # Reconstruct base name
                # distinct files: 
                # 01_strategy_lead_agent.md
                # 01_strategy_lead_agent_state.json
                # 01_strategy_lead_agent_open_questions.json
                # 01_strategy_lead_agent_PROMPT.txt (ignore)
                
                # identify the base name by removing suffixes
                base_name = item.stem
                if base_name.endswith('_state'):
                    base_name = base_name[:-6] # remove _state
                elif base_name.endswith('_open_questions'):
                    base_name = base_name[:-15] # remove _open_questions
                elif base_name.endswith('_PROMPT'):
                    continue # ignore prompt text files

                # Check for .md extension for the main markdown file
                if item.suffix == '.md':
                    # base_name is already correct for .md file usually
                    pass
                
                if base_name not in agents:
                    agents[base_name] = {}
                
                if item.suffix == '.md':
                    agents[base_name]['markdown'] = item
                elif item.name.endswith('_state.json'):
                    agents[base_name]['state'] = item
                elif item.name.endswith('_open_questions.json'):
                    agents[base_name]['questions'] = item

    print(f"Found {len(agents)} agents to validate in {outputs_dir}...\n")
    
    success_count = 0
    failure_count = 0

    for agent_name, files in sorted(agents.items()):
        # Check if we have all required files
        if 'markdown' not in files or 'state' not in files or 'questions' not in files:
            print(f"⚠️  Skipping {agent_name}: Missing component files.")
            # print details
            # print(f"   Found: {list(files.keys())}")
            continue

        try:
            # Construct the combined dict
            md_content = files['markdown'].read_text(encoding='utf-8')
            state_content = json.loads(files['state'].read_text(encoding='utf-8'))
            questions_content = json.loads(files['questions'].read_text(encoding='utf-8'))

            combined_output = {
                "deliverable_markdown": md_content,
                "updated_state": state_content,
                "open_questions": questions_content
            }

            # Validate
            validate_agent_output_dict(agent_name, combined_output)
            print(f"✅ {agent_name}: Passed")
            success_count += 1

        except Exception as e:
            print(f"❌ {agent_name}: Failed - {e}")
            failure_count += 1

    print(f"\nSummary: {success_count} passed, {failure_count} failed.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    else:
        # Default to the most recent output directory if not specified
        # But for now, let's hardcode or ask. 
        # I'll default to the one I know exists: outputs/20260130_111822
        directory = "outputs/20260130_111822"
    
    validate_all(directory)

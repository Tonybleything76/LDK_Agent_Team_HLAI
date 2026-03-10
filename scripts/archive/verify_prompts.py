import glob
import sys

def verify_prompts():
    prompt_files = glob.glob("prompts/*/prompt.md")
    errors = []
    
    # Dummy context matching the 3 injected keys
    context = {
        "business_brief": "TEST_BRIEF",
        "sme_notes": "TEST_NOTES",
        "system_state": "TEST_STATE"
    }

    for p in prompt_files:
        try:
            with open(p, "r") as f:
                content = f.read()
            
            # Attempt formatting
            formatted = content.format(**context)
            
            # Check for unescaped { or } by looking for single braces in the output 
            # (Wait, format consumes the braces. If format succeeds, we are mostly good on SyntaxError)
            
            # If we want to be strict and say "No SINGLE braces allowed in output unless they were intended?" 
            # No, if format() works, it means all single braces were placeholders or escaped.
            # If there was a single brace not in placeholders, format() raises KeyError or ValueError.
            
            print(f"[PASS] {p}")

        except Exception as e:
            errors.append(f"[FAIL] {p}: {str(e)}")

    if errors:
        print("\nERRORS FOUND:")
        for e in errors:
            print(e)
        sys.exit(1)
    else:
        print("\nAll prompts verified successfully!")
        sys.exit(0)

if __name__ == "__main__":
    verify_prompts()

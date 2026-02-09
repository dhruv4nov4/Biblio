"""
Structure Refinement Prompts: Updates the file structure based on user's preferred tech stack.
"""

STRUCTURE_REFINEMENT_SYSTEM_PROMPT = """You are a Technical Architect. Your job is to update the file structure of a project to match a specific Technology Stack requested by the user.

CRITICAL RULE: KEEP IT SIMPLE AND FLAT.
- Do NOT create nested folders like `src`, `templates`, `static`, `public` unless absolutely necessary.
- Prefer putting all files in the root directory.
- Example for Python: `app.py`, `index.html`, `requirements.txt`.
- Example for Node: `server.js`, `index.html`, `package.json`.
- Example for HTML: `index.html`, `style.css`, `script.js`.

- **CRITICAL**: Make sure do not create any extra file for CSS and JS(Client Side). For full stck required applications always put HTML, CSS in single index.html file and backend should be another extra file like for python app.py and for node server.js

The user wants the MINIMAL viable structure for their chosen stack.
"""

def build_structure_refinement_prompt(user_query: str, project_features: list, tech_stack: str) -> str:
    """Construct the prompt for refining file structure."""
    
    features_list = "\n".join([f"- {f['name']}: {f['description']}" for f in project_features])
    
    return f"""{STRUCTURE_REFINEMENT_SYSTEM_PROMPT}

PROJECT CONTEXT:
Query: {user_query}

APPROVED FEATURES:
{features_list}

USER'S CHOSEN TECH STACK:
"{tech_stack}"

TASK:
Generate the new file structure for this specific tech stack.
- If the stack is Python/Flask, include `requirements.txt`.
- If the stack is Node/Express, include `package.json`.
- Keep the number of files to the absolute minimum needed to run the app.

Response Format (JSON only):
{{
  "file_structure": [
    {{
      "name": "filename.ext",
      "type": "code | data | check",
      "purpose": "Brief description",
      "prompt": "Instructions for the builder"
    }}
  ]
}}
"""

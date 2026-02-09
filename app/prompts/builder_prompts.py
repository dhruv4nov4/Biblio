"""
Builder Prompts: Generates actual executable code.
The Builder is a factory worker - follows the Architect's blueprint and USER APPROVALS strictly.

ENHANCED FOR HITL: Uses user-approved features and specifications for 100% accuracy.
"""

BUILDER_SYSTEM_PROMPT = """You are The Builder - a PRECISE code generation specialist.

════════════════════════════════════════════════════════════════
                    CRITICAL MISSION
════════════════════════════════════════════════════════════════

You are generating code for a project where the USER has EXPLICITLY REVIEWED AND APPROVED:
1. Every single feature to implement
2. The exact design specifications (colors, fonts, layout)
3. The technology stack to use
4. The file structure

Your job is to TRANSLATE these approved specifications into PERFECT, WORKING CODE.
This is NOT a suggestion - the user CONFIRMED they want EXACTLY this.

════════════════════════════════════════════════════════════════
                    ABSOLUTE RULES
════════════════════════════════════════════════════════════════

1. ✅ IMPLEMENT 100% OF APPROVED FEATURES
   - Every single approved feature MUST be working in the final code
   - No feature can be skipped or partially implemented
   - If a feature says "Dark Mode Toggle" - there MUST be a working toggle

2. ✅ FOLLOW DESIGN SPECS EXACTLY
   - If color scheme says "Dark theme with cyan (#00d4ff)" - use those EXACT colors
   - If typography says "Inter font" - include the Google Fonts import
   - Match animations and transitions as described

3. ❌ NEVER USE PLACEHOLDERS
   - No "<!-- Add content here -->" 
   - No "// TODO: implement this"
   - No "Lorem ipsum" for real content areas
   - Generate REAL, MEANINGFUL content

4. ❌ NEVER INVENT LIBRARIES
   - Use ONLY the CDN links provided in the asset manifest
   - If no library is provided, use vanilla JavaScript
   - Never hallucinate library methods or APIs

5. ✅ WRITE PRODUCTION-READY CODE
   - Clean, well-commented code
   - Mobile-responsive CSS (flexbox/grid + media queries)
   - Proper error handling in JavaScript
   - Semantic HTML5 tags
   - Accessibility attributes (alt tags, ARIA where needed)

════════════════════════════════════════════════════════════════
                    OUTPUT FORMAT
════════════════════════════════════════════════════════════════

Return ONLY the raw code for the requested file.
- No markdown code blocks (no ```html```)
- No explanations before or after
- Just pure code that can be directly saved to a file

════════════════════════════════════════════════════════════════
                CHAIN OF THOUGHT PLANNING (INTERNAL)
════════════════════════════════════════════════════════════════

Before generating code, you MUST mentally perform these steps:
1. ANALYZE context: What is this file's role? (e.g., "This is the frontend that calls the backend")
2. CHECK INTEGRATION: 
   - If I am `index.html`, where is `app.py` serving me? What API endpoints exist?
   - If I am `app.py`, what static files do I need to serve?
3. PLAN STRUCTURE: Defined imports, classes, and functions required by features.
4. EXECUTE: Write the code based on the strict analysis.
"""


BUILDER_FEATURE_EMPHASIS = """
╔══════════════════════════════════════════════════════════════╗
║        ⚠️  USER-APPROVED FEATURES - MUST IMPLEMENT ALL       ║
╚══════════════════════════════════════════════════════════════╝

The following features have been REVIEWED AND CONFIRMED by the user.
They explicitly said "YES, I want these features" - so you MUST implement ALL of them.

{features_section}

VERIFICATION CHECKLIST:
Before generating code, mentally verify that EACH feature above has:
✓ A corresponding UI element (button, form, display, etc.)
✓ Working JavaScript logic
✓ Proper event listeners connected
✓ Visible feedback for user interactions
"""


BUILDER_DESIGN_EMPHASIS = """
╔══════════════════════════════════════════════════════════════╗
║        🎨  USER-APPROVED DESIGN - FOLLOW EXACTLY             ║
╚══════════════════════════════════════════════════════════════╝

The user approved these EXACT design specifications. Do not improvise or change them.

{design_section}

IMPLEMENTATION CHECKLIST:
✓ Use the EXACT color codes specified
✓ Include font imports for specified typography
✓ Structure layout exactly as described
✓ Implement animations/transitions as specified
"""


BUILDER_TECHSTACK_EMPHASIS = """
╔══════════════════════════════════════════════════════════════╗
║        🛠️  USER-APPROVED TECH STACK                          ║
╚══════════════════════════════════════════════════════════════╝

Tech Stack: {tech_stack}
Approach: {approach_description}

CRITICAL INTEGRATION RULES (STRICT COMPLIANCE REQUIRED):

1. IF FULLSTACK (Python Backend + HTML Frontend):
   - **BACKEND (app.py/main.py)**: 
     - MUST serve `index.html` at the root URL (`/`).
     - MUST serve static files (css/js) correctly.
     - MUST enable CORS (Cross-Origin Resource Sharing).
     - Example Flask: `@app.route('/') def index(): return send_from_directory('.', 'index.html')`
     - Example FastAPI: `app.mount("/static", StaticFiles(...))` AND root route returning FileResponse('index.html').
   
   - **FRONTEND (index.html/script.js)**:
     - MUST use RELATIVE URLs for API calls (e.g., `fetch('/api/tasks')`, NOT `fetch('http://localhost:5000/...')`).
     - MUST NOT use hardcoded localhost ports.
     - MUST NOT contain business logic (calculation, filtering) - call the API!

2. IF FRONTEND-ONLY:
   - All logic must be in the browser (JS).
   - No server-side calls unless using external public APIs.

This is the user's CHOSEN technology - use it correctly.
"""


BUILDER_USER_REQUIREMENTS = """
╔══════════════════════════════════════════════════════════════╗
║        📝  ADDITIONAL USER REQUIREMENTS                       ║
╚══════════════════════════════════════════════════════════════╝

The user added these specific notes/requirements:

"{user_requirements}"

These are EXPLICIT user preferences - prioritize them in your implementation.
"""


FEW_SHOT_EXAMPLES = [
    {
        "file_spec": {
            "name": "index.html",
            "type": "html",
            "prompt": "Create a simple counter app with increment, decrement, and reset buttons",
            "assets": []
        },
        "response": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Counter App</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .container {
            background: white;
            padding: 3rem;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            text-align: center;
        }
        h1 { color: #333; margin-bottom: 2rem; }
        #counter {
            font-size: 4rem;
            font-weight: bold;
            color: #667eea;
            margin: 2rem 0;
        }
        .btn-group { display: flex; gap: 1rem; justify-content: center; }
        button {
            padding: 1rem 2rem;
            font-size: 1rem;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            transition: transform 0.2s;
        }
        button:hover { transform: scale(1.05); }
        .btn-inc { background: #4CAF50; color: white; }
        .btn-dec { background: #f44336; color: white; }
        .btn-reset { background: #9E9E9E; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Counter App</h1>
        <div id="counter">0</div>
        <div class="btn-group">
            <button class="btn-dec" onclick="decrement()">- Decrement</button>
            <button class="btn-reset" onclick="reset()">Reset</button>
            <button class="btn-inc" onclick="increment()">+ Increment</button>
        </div>
    </div>
    <script>
        let count = 0;
        const counterEl = document.getElementById('counter');
        
        function updateDisplay() {
            counterEl.textContent = count;
        }
        
        function increment() {
            count++;
            updateDisplay();
        }
        
        function decrement() {
            count--;
            updateDisplay();
        }
        
        function reset() {
            count = 0;
            updateDisplay();
        }
    </script>
</body>
</html>"""
    }
]


def build_code_generation_prompt(
    file_spec: dict,
    asset_manifest: list,
    user_query: str,
    project_features: list = None,
    design_specs: dict = None,
    # HITL: User-approved content (takes priority)
    approved_features: list = None,
    approved_design_specs: dict = None,
    approved_tech_stack: str = None,
    approved_file_structure: list = None,
    user_requirements: str = None,
    # Retry context
    syntax_errors: list = None
) -> str:
    """
    Construct prompt for generating a specific file.
    
    HITL Enhancement: Prioritizes user-approved content over architect suggestions
    for maximum accuracy.
    """
    
    # Determine which features to use (approved takes priority)
    features_to_use = approved_features if approved_features else project_features
    design_to_use = approved_design_specs if approved_design_specs else design_specs
    
    # Format asset manifest
    assets_text = "No external libraries required. Use vanilla JavaScript only."
    if asset_manifest:
        assets_text = "REQUIRED CDN LINKS (You MUST use these exact URLs):\n"
        for asset in asset_manifest:
            assets_text += f"• {asset['name']}: {asset['url']}\n"
            if asset.get('purpose'):
                assets_text += f"  Purpose: {asset['purpose']}\n"
    
    # Format features with emphasis
    features_text = ""
    if features_to_use and len(features_to_use) > 0:
        # Separate core and enhancement features
        core_features = [f for f in features_to_use if f.get('priority') == 'core']
        enhancement_features = [f for f in features_to_use if f.get('priority') == 'enhancement']
        
        features_section = ""
        
        if core_features:
            features_section += "🔴 CORE FEATURES (ABSOLUTELY REQUIRED - App is broken without these):\n\n"
            for i, feature in enumerate(core_features, 1):
                features_section += f"   {i}. {feature.get('name', 'Feature')}\n"
                features_section += f"      What it does: {feature.get('description', 'No description')}\n"
                features_section += f"      User expects: {feature.get('user_benefit', 'Must work correctly')}\n\n"
        
        if enhancement_features:
            features_section += "\n🟡 ENHANCEMENT FEATURES (Required for polished experience):\n\n"
            for i, feature in enumerate(enhancement_features, 1):
                features_section += f"   {i}. {feature.get('name', 'Feature')}\n"
                features_section += f"      What it does: {feature.get('description', 'No description')}\n"
                features_section += f"      User expects: {feature.get('user_benefit', 'Should work well')}\n\n"
        
        features_text = BUILDER_FEATURE_EMPHASIS.format(features_section=features_section)
    
    # Format design specifications with emphasis
    design_text = ""
    if design_to_use and len(design_to_use) > 0:
        design_section = ""
        
        if design_to_use.get('color_scheme'):
            design_section += f"🎨 COLOR SCHEME:\n   {design_to_use['color_scheme']}\n\n"
        
        if design_to_use.get('typography'):
            design_section += f"✒️  TYPOGRAPHY:\n   {design_to_use['typography']}\n\n"
        
        if design_to_use.get('layout'):
            design_section += f"📐 LAYOUT:\n   {design_to_use['layout']}\n\n"
        
        if design_to_use.get('animations'):
            design_section += f"✨ ANIMATIONS:\n   {design_to_use['animations']}\n\n"
        
        design_text = BUILDER_DESIGN_EMPHASIS.format(design_section=design_section)
    
    # Format tech stack context
    tech_stack_text = ""
    if approved_tech_stack:
        approach_map = {
            # Frontend-only stacks
            "html_single": "Single HTML file with embedded CSS and JavaScript. Everything in one file.",
            "html_multi": "Multiple HTML files with shared CSS. Navigation between pages.",
            "react_cdn": "React application loaded via CDN. Use React.createElement or JSX via Babel.",
            "vue_cdn": "Vue application loaded via CDN. Use Vue's template syntax.",
            # Python backend stacks
            "python_flask": "Python Flask backend with REST API. Include requirements.txt with all dependencies.",
            "python_fastapi": "Python FastAPI backend with async endpoints. Include requirements.txt with all dependencies.",
            # Node.js backend stacks
            "node_express": "Node.js Express backend. Include package.json with all dependencies and npm scripts.",
            # Fullstack stacks
            "fullstack_python": "Full-stack app with HTML frontend and Python Flask/FastAPI backend. Include requirements.txt.",
            "fullstack_node": "Full-stack app with HTML frontend and Node.js Express backend. Include package.json."
        }
        tech_stack_text = BUILDER_TECHSTACK_EMPHASIS.format(
            tech_stack=approved_tech_stack,
            approach_description=approach_map.get(approved_tech_stack, f"Custom stack: {approved_tech_stack}. Generate appropriate files based on the user's description.")
        )
    
    # Format user requirements
    requirements_text = ""
    if user_requirements and user_requirements.strip():
        requirements_text = BUILDER_USER_REQUIREMENTS.format(user_requirements=user_requirements)

    # Format file structure context (CoT enabler)
    file_context_text = ""
    if approved_file_structure:
        file_list = "\n".join([f"- {f['name']} ({f.get('purpose', 'file')})" for f in approved_file_structure])
        file_context_text = f"""
╔══════════════════════════════════════════════════════════════╗
║        📁  PROJECT FILE CONTEXT (The Full Picture)           ║
╚══════════════════════════════════════════════════════════════╝

You are building ONE file in this larger project:
{file_list}

INTEGRATION REMINDER:
- Check the list above. If you are building the frontend, look for the backend file.
- If you are building the backend, remember to serve the frontend file.
"""
    
    # Format retry context
    retry_context = ""
    if syntax_errors:
        retry_context = f"""
╔══════════════════════════════════════════════════════════════╗
║        ⚠️  PREVIOUS VERSION HAD ERRORS - FIX THEM            ║
╚══════════════════════════════════════════════════════════════╝

The previous code had these issues. Fix them in this version:

"""
        for error in syntax_errors:
            retry_context += f"  ❌ {error}\n"
        retry_context += "\nEnsure the new version does NOT have these problems."
    
    # Build the complete prompt
    prompt = f"""{BUILDER_SYSTEM_PROMPT}

{assets_text}
{features_text}
{design_text}
{tech_stack_text}
{file_context_text}
{requirements_text}

════════════════════════════════════════════════════════════════
                    FILE TO GENERATE
════════════════════════════════════════════════════════════════

📄 Filename: {file_spec['name']}
📁 Type: {file_spec['type']}
📋 Instructions: {file_spec.get('prompt', 'Generate this file according to specifications')}

════════════════════════════════════════════════════════════════
                    ORIGINAL USER REQUEST
════════════════════════════════════════════════════════════════

"{user_query}"
{retry_context}

════════════════════════════════════════════════════════════════
                    GENERATE CODE NOW
════════════════════════════════════════════════════════════════

Generate the COMPLETE, WORKING code for {file_spec['name']}.
Remember: Every approved feature must work. Every design spec must be followed.

Code for {file_spec['name']}:"""

    return prompt
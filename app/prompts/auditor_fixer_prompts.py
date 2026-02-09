"""
Auditor (Code Fixer) Prompts: Surgical code fixes based on validation issues.
The Auditor is a SURGICAL CODE SURGEON - makes PRECISE fixes, NEVER regenerates entire files.
"""

AUDITOR_FIXER_SYSTEM_PROMPT = """You are The Code Surgeon - a PRECISION code fixer.

Your mission: Fix SPECIFIC issues identified by the Syntax Guard with SURGICAL PRECISION.

════════════════════════════════════════════════════════════════════════════════
                        ABSOLUTE RULES (CRITICAL)
════════════════════════════════════════════════════════════════════════════════

1. ❌ **NEVER REGENERATE ENTIRE FILES**
   - You are NOT a code generator
   - You are a CODE FIXER
   - Only modify the SPECIFIC lines mentioned in issues

2. ✅ **SURGICAL FIXES ONLY**
   - Issue says "Line 42: change 'userName' to 'username'" → Change ONLY that line
   - Issue says "Add CORS" → Add ONLY the CORS import and initialization
   - Issue says "Fix endpoint mismatch" → Change ONLY the endpoint URL/route

3. ✅ **PRESERVE EXISTING CODE**
   - Keep all working code unchanged
   - Maintain original code style and formatting
   - Don't "improve" code that isn't broken
   - Don't refactor unless specifically asked

4. ✅ **FIX ALL ISSUES**
   - Address EVERY issue provided by Syntax Guard
   - Fix in order of severity (CRITICAL first)
   - Ensure fixes don't create NEW issues

5. ✅ **PROVIDE CONTEXT**
   - Show BEFORE and AFTER for each fix
   - Explain WHY the fix resolves the issue
   - Confirm fix is minimal and targeted

════════════════════════════════════════════════════════════════════════════════
                        FIX PATTERNS (EXAMPLES)
════════════════════════════════════════════════════════════════════════════════

**Example 1: HTML ID Mismatch**

Issue: "HTML uses id='taskInput' but JS uses getElementById('task-input')"

WRONG APPROACH ❌:
- Regenerate entire index.html file

RIGHT APPROACH ✅:
- Find: <input id="taskInput">
- Replace: <input id="task-input">
- DONE (1 line changed)

**Example 2: API Endpoint Mismatch**

Issue: "Frontend calls fetch('/api/tasks') but backend has '/api/todos'"

WRONG APPROACH ❌:
- Rewrite entire app.py with all routes

RIGHT APPROACH ✅:
- Find: @app.route('/api/todos')
- Replace: @app.route('/api/tasks')
- DONE (1 line changed)

**Example 3: Missing CORS**

Issue: "Fullstack app but backend doesn't enable CORS"

WRONG APPROACH ❌:
- Regenerate Flask app from scratch

RIGHT APPROACH ✅:
- Add after imports: from flask_cors import CORS
- Add after app = Flask(__name__): CORS(app)
- DONE (2 lines added)

**Example 4: Missing Import**

Issue: "Code uses 'json' module but no import statement"

RIGHT APPROACH ✅:
- Add at top: import json
- DONE (1 line added)

════════════════════════════════════════════════════════════════════════════════
                        OUTPUT FORMAT (STRICT JSON)
════════════════════════════════════════════════════════════════════════════════

Return a JSON object with this EXACT structure:

{{
  "fixes_applied": [
    {{
      "issue_id": 1,
      "file": "index.html",
      "issue_category": "INTEGRATION_ISSUE",
      "fix_type": "REPLACE",
      "location": "Line 42",
      "before": "<input id='taskInput' />",
      "after": "<input id='task-input' />",
      "reasoning": "Changed camelCase 'taskInput' to hyphenated 'task-input' to match JavaScript selector getElementById('task-input')",
      "lines_changed": 1
    }},
    {{
      "issue_id": 2,
      "file": "app.py",
      "issue_category": "MISSING_IMPORT",
      "fix_type": "ADD",
      "location": "After line 1",
      "before": "from flask import Flask",
      "after": "from flask import Flask\\nfrom flask_cors import CORS",
      "reasoning": "Added CORS import to enable cross-origin requests for fullstack app",
      "lines_changed": 1
    }}
  ],
  
  "fixed_code": {{
    "index.html": "<!DOCTYPE html>\\n<html lang='en'>\\n<head>\\n  <meta charset='UTF-8'>\\n  <title>Todo App</title>\\n</head>\\n<body>\\n  <input id='task-input' />\\n  <button onclick='addTask()'>Add</button>\\n</body>\\n</html>",
    "app.py": "from flask import Flask\\nfrom flask_cors import CORS\\n\\napp = Flask(__name__)\\nCORS(app)\\n\\n@app.route('/api/tasks')\\ndef get_tasks():\\n    return {{'tasks': []}}\\n\\nif __name__ == '__main__':\\n    app.run()"
  }},
  
  "summary": {{
    "total_issues_fixed": 2,
    "files_modified": ["index.html", "app.py"],
    "files_unchanged": ["script.js"],
    "all_issues_resolved": true
  }}
}}

**CRITICAL: The "fixed_code" section MUST contain the COMPLETE, ENTIRE file content for each file you modify.**
- NOT summaries
- NOT placeholders like "... rest of code ..."
- NOT excerpts
- THE FULL FILE FROM START TO END

**ONLY include files that need fixes. Do NOT add files that weren't in the original generated code.**

FIX TYPES:
- **REPLACE**: Replace existing code (e.g., rename variable)
- **ADD**: Add new code (e.g., add import, add CORS)
- **DELETE**: Remove code (e.g., remove debug statements)
- **REORDER**: Move code to different location

════════════════════════════════════════════════════════════════════════════════
                        VERIFICATION CHECKLIST
════════════════════════════════════════════════════════════════════════════════

Before returning fixes, verify:

□ Did I fix ALL issues from Syntax Guard?
□ Are my fixes MINIMAL (changed only what's necessary)?
□ Did I preserve ALL working code?
□ Will my fixes create NEW issues? (cross-check)
□ Is the fixed code syntactically valid?
□ Did I include COMPLETE fixed code for each modified file?

If ANY checkbox is unchecked, revise your fixes.

════════════════════════════════════════════════════════════════════════════════
                        CRITICAL PRINCIPLES
════════════════════════════════════════════════════════════════════════════════

1. **Minimal Change Principle**
   - Change the LEAST amount of code possible
   - One-line issue = one-line fix

2. **Surgical Precision Principle**
   - Target the EXACT problematic code
   - Don't touch surrounding code

3. **No Scope Creep Principle**
   - Fix ONLY what Syntax Guard identified
   - Don't "improve" other parts of code

4. **Completeness Principle**
   - Fix ALL issues, not just some
   - Ensure fixes don't conflict with each other

You are a SURGEON, not a BUILDER. Act accordingly.
"""


def build_auditor_fixer_prompt(
    generated_code: dict,
    file_structure: list,
    syntax_guard_issues: dict,
    user_query: str
) -> str:
    """
    Build surgical fix prompt with all context.
    
    This prompt includes:
    - Original generated code
    - All issues identified by Syntax Guard
    - File structure for context
    - Original user intent
    """
    
    # Format original code
    code_section = "ORIGINAL CODE (GENERATED BY BUILDER):\n"
    code_section += "=" * 80 + "\n\n"
    for filename, code in generated_code.items():
        code_section += f"📄 FILE: {filename}\n"
        code_section += "-" * 80 + "\n"
        # Add line numbers for precision
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            code_section += f"{i:4d} | {line}\n"
        code_section += "-" * 80 + "\n\n"
    
    # Format issues from Syntax Guard
    issues_section = "ISSUES IDENTIFIED BY SYNTAX GUARD:\n"
    issues_section += "=" * 80 + "\n\n"
    
    if syntax_guard_issues.get("issues"):
        for i, issue in enumerate(syntax_guard_issues["issues"], 1):
            issues_section += f"ISSUE #{i}:\n"
            issues_section += f"  Category: {issue.get('category', 'N/A')}\n"
            issues_section += f"  Severity: {issue.get('severity', 'N/A')}\n"
            issues_section += f"  File: {issue.get('file', 'N/A')}\n"
            issues_section += f"  Location: {issue.get('location', 'N/A')}\n"
            issues_section += f"  Issue: {issue.get('issue', 'N/A')}\n"
            issues_section += f"  Reasoning: {issue.get('reasoning', 'N/A')}\n"
            issues_section += f"  Suggested Fix: {issue.get('suggested_fix', 'N/A')}\n"
            if issue.get('related_files'):
                issues_section += f"  Related Files: {', '.join(issue['related_files'])}\n"
            issues_section += "\n"
    else:
        issues_section += "No issues found (validation passed).\n"
    
    # Format Syntax Guard's chain of thought
    cot_section = ""
    if syntax_guard_issues.get("chain_of_thought"):
        cot = syntax_guard_issues["chain_of_thought"]
        cot_section = "\nSYNTAX GUARD'S ANALYSIS:\n"
        cot_section += "=" * 80 + "\n"
        cot_section += f"Architecture: {cot.get('architecture', 'N/A')}\n"
        cot_section += f"Mismatches Found: {cot.get('mismatches_found', 0)}\n\n"
        
        if cot.get("integration_points"):
            ip = cot["integration_points"]
            cot_section += "Integration Points Mapped:\n"
            cot_section += f"  HTML IDs: {ip.get('html_ids', [])}\n"
            cot_section += f"  JS Selectors: {ip.get('js_selectors', [])}\n"
            cot_section += f"  Frontend Endpoints: {ip.get('frontend_endpoints', [])}\n"
            cot_section += f"  Backend Routes: {ip.get('backend_routes', [])}\n"
            cot_section += f"  Imports: {ip.get('imports', [])}\n"
            cot_section += f"  Dependencies: {ip.get('dependencies', [])}\n"
    
    # Format file structure
    structure_section = "\nFILE STRUCTURE:\n"
    structure_section += "=" * 80 + "\n"
    for spec in file_structure:
        structure_section += f"- {spec.get('name', 'Unknown')} ({spec.get('type', 'unknown')})\n"
    
    # Summary from Syntax Guard
    summary_section = ""
    if syntax_guard_issues.get("summary"):
        summary = syntax_guard_issues["summary"]
        summary_section = f"""
SUMMARY FROM SYNTAX GUARD:
{'=' * 80}
Total Issues: {summary.get('total_issues', 0)}
Critical Issues: {summary.get('critical_issues', 0)}
Files Affected: {', '.join(summary.get('files_affected', []))}
Validation Result: {summary.get('validation_result', 'UNKNOWN')}
"""
    
    # Build complete prompt
    prompt = f"""{AUDITOR_FIXER_SYSTEM_PROMPT}

════════════════════════════════════════════════════════════════════════════════
                        FIXING TASK
════════════════════════════════════════════════════════════════════════════════

ORIGINAL USER REQUEST:
"{user_query}"

{structure_section}

{cot_section}

{summary_section}

{issues_section}

{code_section}

════════════════════════════════════════════════════════════════════════════════
                        YOUR TASK
════════════════════════════════════════════════════════════════════════════════

Fix ALL issues listed above with SURGICAL PRECISION.

For EACH issue:
1. Locate the EXACT problematic code (use line numbers)
2. Determine the MINIMAL fix needed
3. Apply the fix WITHOUT touching surrounding code
4. Verify the fix resolves the issue

Return:
1. List of ALL fixes applied (before/after for each)
2. COMPLETE fixed code for EACH modified file
3. Summary of what was fixed

CRITICAL REMINDERS:
- Do NOT regenerate entire files from scratch
- Change ONLY the specific problematic lines
- Preserve ALL working code
- Fix ALL issues (don't skip any)
- In "fixed_code", provide the COMPLETE modified file (every single line)
- ONLY include files that exist in ORIGINAL CODE section above
- Do NOT add files that weren't generated (e.g., if no script.js was generated, don't create one)
- If an issue mentions a non-existent file, mark it as false positive

Return ONLY valid JSON with your fixes.

FIXED CODE:"""

    return prompt

"""
Dependency Analyzer Node: Analyzes generated code and creates accurate dependency files using LLM.

This node uses the Auditor LLM (Llama 3 70b) to intelligently scan code and generate 
requirements.txt/package.json based on ACTUAL usage patterns, avoiding hallucinations.
"""

import json
from typing import Dict, List, Any
from langchain_core.messages import SystemMessage, HumanMessage
from app.models.state import BuilderState
from app.core.llm_factory import llm_factory
from app.utils.logger import get_logger
from app.utils.parsers import parse_llm_json

logger = get_logger(__name__)

DEPENDENCY_SYSTEM_PROMPT = """You are a Senior Dependency Manager & Integration Specialist.
Your job is to analyze the source code of a web project and generate the EXACT dependency files needed.

════════════════════════════════════════════════════════════════
                        CRITICAL RULES
════════════════════════════════════════════════════════════════

1. 🐍 PYTHON PROJECTS (Flask/FastAPI/Django):
   - READ the imports in .py files (e.g., `import flask`, `from fastapi import FastAPI`).
   - GENERATE `requirements.txt` containing ONLY the packages actually verified in the code.
   - For `fastapi`, ALWAYS include `uvicorn[standard]` and `pydantic`.
   - For `flask`, ALWAYS include `gunicorn` (for prod) if not specified.
   - DO NOT hallucinate packages that are not used (e.g., if no database code, do not add sqlalchemy).

2. 📦 NODE.JS PROJECTS (Express/React/Vue):
   - READ `require(...)` or `import ... from ...` in .js/.ts files.
   - GENERATE `package.json` with appropriate `dependencies` and `scripts` ("start": "node index.js").
   - DO NOT generate package.json for pure frontend projects (standard HTML/JS) unless they explicitly use npm packages.

3. ❌ AVOID HALLUCINATIONS:
   - If the project is HTML/CSS/JS only (no backend), do NOT generate `requirements.txt`.
   - If the user asked for Flask, do NOT add FastAPI dependencies.
   - Use standard, compatible versions (e.g., `flask>=3.0.0`).

4. 🔍 JSON OUTPUT ONLY:
   Return a single JSON object with the filenames as keys and file content as values.
   If a file is not needed, set its value to null.

EXAMPLE OUTPUT:
{
  "requirements.txt": "flask>=3.0.0\\nflask-cors>=4.0.0\\ngunicorn>=21.2.0",
  "package.json": null
}
"""


def dependency_analyzer_node(state: BuilderState) -> BuilderState:
    """
    Analyze generated files and create accurate dependency files using LLM.
    """
    logger.info("🔍 Dependency Analyzer (LLM): Starting analysis...")
    
    # FIX: The state uses "generated_code" not "generated_files"
    generated_files = state.get("generated_code", {})
    
    if not generated_files:
        logger.warning("No generated files to analyze")
        return {**state, "current_node": "dependency_analyzer"}
    
    # Prepare file context for LLM
    # We limit content to first 500 lines per file to fit context if needed, 
    # but 70b model handles large context well.
    files_context = ""
    for name, content in generated_files.items():
        files_context += f"--- START OF FILE: {name} ---\n"
        files_context += content[:15000] # Limit char count just in case
        files_context += f"\n--- END OF FILE: {name} ---\n\n"
        
    # Use APPROVED tech stack from user's checkpoint approval
    tech_stack = state.get("approved_tech_stack") or state.get("tech_stack", "unknown")
    logger.info(f"📊 Analyzing dependencies for stack: {tech_stack}")
    
    # check for existing dependency files to avoid overwriting if they are already good? 
    # Actually, user wants us to fix them, so we should regenerate or check them.
    # We'll let LLM decide.

    prompt_content = f"""
PROJECT TECH STACK: {tech_stack}

SOURCE CODE FILES:
{files_context}

Task: Identify the tech stack used in the code above and generate the necessary dependency files.
Return ONLY valid JSON.
"""

    messages = [
        SystemMessage(content=DEPENDENCY_SYSTEM_PROMPT),
        HumanMessage(content=prompt_content)
    ]
    
    try:
        # Use Auditor LLM (Llama 3 70b is great for strict analysis)
        llm = llm_factory.get_auditor_llm()
        response = llm.invoke(messages)
        
        # Parse JSON
        result = parse_llm_json(response.content)
        
        new_files = {}
        
        # Process requirements.txt
        if result.get("requirements.txt"):
            content = result["requirements.txt"].strip()
            if content and len(content) > 5: # Basic validity check
                new_files["requirements.txt"] = content
                logger.info(f"✅ Generated requirements.txt ({len(content.splitlines())} lines)")

        # Process package.json
        if result.get("package.json"):
            # Ensure it's a string
            content = result["package.json"]
            if isinstance(content, dict):
                content = json.dumps(content, indent=2)
            
            if content and len(content) > 10:
                new_files["package.json"] = content
                logger.info("✅ Generated package.json")
        
        if not new_files:
            logger.info("ℹ️ No dependency files needed or detected.")
        
        # Merge new files
        updated_files = {**generated_files, **new_files}
        
        return {
            **state,
            "generated_code": updated_files,  # FIX: Use correct field name
            "current_node": "dependency_analyzer",
            # We can store analysis if needed
            "dependency_analysis": {"generated": list(new_files.keys())}
        }
        
    except Exception as e:
        logger.error(f"❌ Dependency Analyzer Failed: {str(e)}")
        # Fallback: Don't crash, just return original state
        return {
            **state, 
            "current_node": "dependency_analyzer",
            "errors": [f"Dependency analysis failed: {str(e)}"] + state.get("errors", [])
        }

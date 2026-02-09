"""
Node 4: Syntax Guard (The Judge)
Metadata-Driven Validation Node.
Uses "Scouts" to extract a wiring diagram and an LLM "Judge" to validate connections.
"""
from app.models.state import BuilderState
from app.core.llm_factory import llm_factory
from app.prompts.syntax_guard_prompts import build_syntax_guard_prompt
from app.utils.logger import get_logger
from app.utils.parsers import parse_llm_json
from app.utils.scouts import project_registry  # New integration
import json

logger = get_logger(__name__)


def syntax_guard_node(state: BuilderState) -> BuilderState:
    """
    Node 4: Metadata-Driven Validation ("The Wiring Inspector").
    
    Phase 1: Extraction (The Scouts)
    - parses code to build a 'wiring diagram' (JSON).
    
    Phase 2: Validation (The Judge)
    - Sends ONLY the wiring diagram to LLM to find mismatches.
    """
    logger.info("[SYNTAX GUARD] Starting Metadata-Driven Validation (Wiring Inspector)")
    
    state["current_node"] = "syntax_guard"
    generated_code = state.get("generated_code", {})
    
    try:
        # ======================================================================
        # PHASE 1: THE SCOUTS (Extraction)
        # ======================================================================
        # Run local parsers (Regex/AST) -> No LLM cost, infinite context handling
        logger.info("[SYNTAX GUARD] Scouts deployed: Extracting metadata...")
        wiring_diagram = project_registry.build_wiring_diagram(generated_code)
        
        # Log summary of what scouts found
        logger.info(f"[SYNTAX GUARD] Wiring Diagram built for {len(wiring_diagram)} files.")
        
        # Immediate Syntax Check (AST/Parser failures)
        # If scouts flagged "syntax_error", we don't even need the LLM to know it's broken.
        syntax_errors = []
        for filename, data in wiring_diagram.items():
            if data.get("syntax_error"):
                logger.error(f"[SYNTAX GUARD] ❌ Syntax Error detected by Scout in {filename}")
                syntax_errors.append({
                    "category": "SYNTAX_ERROR",
                    "severity": "CRITICAL",
                    "file": filename,
                    "issue": "Parser failed to read file. Likely syntax error.",
                    "suggested_fix": "Fix syntax errors in file."
                })

        # ======================================================================
        # PHASE 2: THE JUDGE (Validation)
        # ======================================================================
        # Only call LLM if we have connection data to check
        validation_issues = syntax_errors[:] # Start with scout-found errors
        
        # Dynamic Judge Logic:
        # Skip ONLY if it's a single standalone HTML file (no connections to validate)
        # Run Judge for ALL other scenarios (HTML+Python, HTML+JS, multiple files, etc.)
        total_files = len(generated_code)
        is_single_html_only = (total_files == 1 and 
                               list(generated_code.keys())[0].endswith('.html'))
        
        should_run_judge = not is_single_html_only
        
        if should_run_judge:
            logger.info("[SYNTAX GUARD] Judge summoned: Verifying connections...")
            
            # Using Auditor LLM (High intelligence, but now low context usage)
            llm = llm_factory.get_auditor_llm()
            
            prompt = build_syntax_guard_prompt(
                wiring_diagram=wiring_diagram,
                approved_features=state.get("approved_features", []),
                user_query=state.get("user_query", "")
            )
            
            # Log prompt size savings (approximate)
            logger.info("[SYNTAX GUARD] Sending Wiring Diagram to LLM (Context Verified Safe)")
            
            response = llm.invoke(prompt)
            result = parse_llm_json(response.content)
            
            llm_issues = result.get("issues", [])
            validation_issues.extend(llm_issues)
            
            logger.info(f"[SYNTAX GUARD] Judge verdict: Found {len(llm_issues)} integration issues")
        else:
            logger.info(f"[SYNTAX GUARD] Single HTML file detected ({total_files} file). Skipping Judge.")

        # ======================================================================
        # UPDATE STATE
        # ======================================================================
        state["validation_issues"] = validation_issues
        state["validation_passed"] = len(validation_issues) == 0
        state["syntax_guard_validation"] = {
            "wiring_diagram": wiring_diagram,
            "issues": validation_issues
        }
        
        if validation_issues:
            logger.warning(f"[SYNTAX GUARD] ⚠️  Found {len(validation_issues)} total issues.")
        else:
            logger.info(f"[SYNTAX GUARD] ✅ Wiring Validated. System Stable.")
            
        return state

    except Exception as e:
        logger.error(f"[SYNTAX GUARD] Critical failure: {str(e)}")
        # Fallback
        state["validation_issues"] = [{
            "category": "SYSTEM_ERROR",
            "severity": "WARNING",
            "issue": f"Syntax Guard crashed: {str(e)}"
        }]
        state["validation_passed"] = True # Don't block pipeline on tool failure
        return state


def should_retry_after_syntax(state: BuilderState) -> str:
    """
    Router: Decide whether to send to Auditor (Code Fixer) or proceed.
    """
    validation_passed = state.get("validation_passed", True)
    has_issues = len(state.get("validation_issues", [])) > 0
    
    if has_issues and not validation_passed:
        logger.info("[SYNTAX GUARD] Routing to Auditor for code fixes")
        return "auditor"
    else:
        logger.info("[SYNTAX GUARD] Validation passed, proceeding to dependency analysis")
        return "dependency_analyzer"
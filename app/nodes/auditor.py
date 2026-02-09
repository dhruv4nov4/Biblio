"""
Node 5: The Code Surgeon (formerly Auditor)
Performs SURGICAL fixes to code based on Syntax Guard findings.
NEVER regenerates entire files - only makes targeted, precise fixes.

ITERATIVE APPROACH: Fixes one file at a time to avoid token limit issues.
"""
from app.models.state import BuilderState
from app.core.llm_factory import llm_factory
from app.prompts.auditor_single_file_prompts import build_single_file_fix_prompt
from app.utils.logger import get_logger
from app.utils.parsers import parse_llm_json
from app.config import settings
from typing import Dict, List

logger = get_logger(__name__)


def auditor_node(state: BuilderState) -> BuilderState:
    """
    Node 5: Surgical Code Fixer - ITERATIVE APPROACH.
    
    Processes ONE file at a time to avoid token limit issues:
    1. Group issues by file
    2. For each file with issues:
       - Send ONLY that file + its issues
       - Get back ONLY that fixed file
       - Update state incrementally
    
    This prevents JSON truncation and ensures reliable fixes.
    """
    logger.info("[CODE SURGEON] Starting iterative surgical code fixes")
    
    state["current_node"] = "auditor"
    
    # Get validation issues from Syntax Guard
    validation_issues = state.get("validation_issues", [])
    generated_code = state.get("generated_code", {}).copy()  # Copy to preserve original
    
    # Filter out issues for files that don't exist
    existing_files = set(generated_code.keys())
    valid_issues = []
    filtered_issues = []
    
    for issue in validation_issues:
        issue_file = issue.get("file", "")
        if issue_file in existing_files:
            valid_issues.append(issue)
        else:
            filtered_issues.append(issue_file)
            logger.warning(f"[CODE SURGEON] Ignoring issue for non-existent file: {issue_file}")
    
    if filtered_issues:
        logger.warning(f"[CODE SURGEON] Filtered out issues for {len(filtered_issues)} non-existent files: {', '.join(set(filtered_issues))}")
    
    # If no valid issues, skip fixing
    if not valid_issues:
        logger.info("[CODE SURGEON] No valid issues to fix - code is already clean!")
        state["code_fixes_applied"] = []
        return state
    
    # Group issues by file
    issues_by_file: Dict[str, List[dict]] = {}
    for issue in valid_issues:
        filename = issue.get("file", "")
        if filename not in issues_by_file:
            issues_by_file[filename] = []
        issues_by_file[filename].append(issue)
    
    logger.info(f"[CODE SURGEON] Grouped {len(valid_issues)} issues across {len(issues_by_file)} files")
    
    # Track all fixes
    all_fixes_applied = []
    files_modified = []
    files_with_errors = []
    
    try:
        # Get LLM for fixing
        llm = llm_factory.get_auditor_llm()
        
        # Process each file iteratively
        for file_idx, (filename, file_issues) in enumerate(issues_by_file.items(), 1):
            logger.info(f"[CODE SURGEON] Processing file {file_idx}/{len(issues_by_file)}: {filename} ({len(file_issues)} issues)")
            
            try:
                # Build prompt for THIS file only
                prompt = build_single_file_fix_prompt(
                    filename=filename,
                    file_code=generated_code.get(filename, ""),
                    file_issues=file_issues,
                    user_query=state.get("user_query", "")
                )
                
                # Get fixes for this file with strict system message
                from langchain_core.messages import HumanMessage, SystemMessage
                
                messages = [
                    SystemMessage(content="You are a JSON-only code fixer. Return ONLY valid JSON. Your first character must be '{' and last character must be '}'. NO explanatory text before or after JSON."),
                    HumanMessage(content=prompt)
                ]
                
                response = llm.invoke(messages)
                fix_result = parse_llm_json(response.content)
                
                # Extract fixed code for THIS file (simplified format)
                fixed_code = fix_result.get("fixed_code", "")
                fixes_summary = fix_result.get("fixes_summary", "")
                
                # Validate fixed code
                if not fixed_code or "... (COMPLETE" in fixed_code or len(fixed_code) < 50:
                    logger.error(f"[CODE SURGEON] Invalid fixed code for {filename} (placeholder or too short), keeping original")
                    continue
                
                # Update generated code with fixed version
                generated_code[filename] = fixed_code
                files_modified.append(filename)
                
                # Store summary for this file
                all_fixes_applied.append({
                    "file": filename,
                    "summary": fixes_summary,
                    "issues_fixed": len(file_issues)
                })
                
                logger.info(f"[CODE SURGEON] ✅ Fixed {filename} - {fixes_summary[:80]}")
                
            except Exception as file_error:
                logger.error(f"[CODE SURGEON] Failed to fix {filename}: {str(file_error)}")
                files_with_errors.append(filename)
                continue
        
        # Update state with all fixed code
        state["generated_code"] = generated_code
        state["code_fixes_applied"] = all_fixes_applied
        state["fix_summary"] = {
            "total_files_fixed": len(files_modified),
            "files_modified": files_modified,
            "files_with_errors": files_with_errors,
            "all_issues_resolved": len(files_with_errors) == 0
        }
        
        # Log summary
        logger.info(f"[CODE SURGEON] Iterative fix complete:")
        logger.info(f"  - Files Fixed: {len(files_modified)}/{len(issues_by_file)}")
        logger.info(f"  - Files Modified: {', '.join(files_modified) if files_modified else 'None'}")
        logger.info(f"  - Files With Errors: {', '.join(files_with_errors) if files_with_errors else 'None'}")
        logger.info(f"  - All Issues Resolved: {'✅ YES' if len(files_with_errors) == 0 else '⚠️ NO'}")
        
        # Log individual file fixes
        if all_fixes_applied:
            logger.info(f"[CODE SURGEON] Fix summaries:")
            for i, fix_info in enumerate(all_fixes_applied, 1):
                logger.info(f"  {i}. {fix_info['file']}: {fix_info['summary'][:80]}")
        
        if files_with_errors:
            logger.warning(f"[CODE SURGEON] ⚠️ {len(files_with_errors)} files had errors during fixing")
        
        return state
        
    except Exception as e:
        logger.error(f"[CODE SURGEON] Fixing failed: {str(e)}")
        # Fallback: keep original code, mark as attempted
        state["code_fixes_applied"] = []
        state["fix_summary"] = {
            "error": str(e),
            "all_issues_resolved": False
        }
        logger.warning("[CODE SURGEON] Proceeding with original code due to fix failure")
        return state


def should_retry_after_audit(state: BuilderState) -> str:
    """
    Router: Always proceed to Dependency Analyzer after fixes.
    
    The old logic (retry on semantic issues) is removed because:
    - Syntax Guard now does comprehensive validation
    - Auditor now does surgical fixes (no validation)
    - No need for retry loop here
    """
    logger.info("[CODE SURGEON] Proceeding to dependency analysis")
    return "dependency_analyzer"
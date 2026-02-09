"""
BuilderState: The shared memory object that flows through the entire graph.
All nodes read from and write to this state.

Enhanced with HITL (Human-in-the-Loop) approval workflow fields.
"""
from typing import TypedDict, List, Dict, Optional, Any


class BuilderState(TypedDict):
    """State object representing the full lifecycle of a build request."""
    
    # ==================== INPUT ====================
    task_id: str
    user_query: str
    reference_url: Optional[str]
    
    # ==================== STRATEGY (Blueprint) ====================
    is_feasible: bool
    classification: Optional[str]  # "HOMEWORK" | "PRODUCTION" | "MALICIOUS"
    refusal_reason: Optional[str]
    
    tech_stack: Optional[str]  # "html_single" | "html_multi" | "react_cdn" | "vue_cdn"
    file_structure: List[Dict[str, str]]  # [{'name': 'index.html', 'prompt': '...', 'type': 'html'}]
    asset_manifest: List[Dict[str, str]]  # [{'type': 'cdn', 'url': 'https://...', 'name': 'Chart.js'}]
    reasoning: Optional[str]  # Architect's reasoning for the chosen approach
    
    # Feature Planning (for UI showcase)
    project_features: List[Dict[str, str]]  # [{'name': 'Feature', 'description': '...', 'priority': 'core|enhancement', 'user_benefit': '...'}]
    design_specs: Optional[Dict[str, str]]  # {'color_scheme': '...', 'typography': '...', 'layout': '...', 'animations': '...'}
    
    # ==================== HITL APPROVAL WORKFLOW ====================
    # Stage tracking
    approval_stage: Optional[str]  # "feature_approval" | "techstack_approval" | "building" | None
    waiting_for_approval: bool  # True when pipeline is paused for user input
    
    # User-approved content (final source of truth for Builder)
    approved_features: List[Dict[str, Any]]  # User's final approved feature list
    approved_design_specs: Optional[Dict[str, str]]  # User's final approved design specs
    approved_tech_stack: Optional[str]  # User's final approved tech stack
    approved_file_structure: List[Dict[str, str]]  # User's final approved file structure
    approved_asset_manifest: List[Dict[str, str]]  # User's final approved dependencies
    
    # User modifications/notes
    user_requirements: Optional[str]  # Additional user requirements/notes
    
    # ==================== EXECUTION (Code) ====================
    generated_code: Dict[str, str]  # {'index.html': '<html>...', 'app.js': '...'}
    
    # ==================== VALIDATION (Syntax Guard - LLM-powered) ====================
    syntax_guard_validation: Optional[Dict[str, Any]]  # Complete validation result with COT
    validation_issues: List[Dict[str, Any]]  # Issues found by Syntax Guard
    validation_passed: bool  # True if no critical issues
    
    # ==================== CODE FIXING (Auditor = Code Surgeon) ====================
    code_fixes_applied: List[Dict[str, Any]]  # Surgical fixes made by Auditor
    fix_summary: Optional[Dict[str, Any]]  # Summary of fixes
    
    # ==================== LEGACY FIELDS (kept for backward compatibility) ====================
    syntax_errors: List[str]  # Old field - may be deprecated
    semantic_issues: List[str]  # Old field - may be deprecated
    retry_count: int
    
    # ==================== OUTPUT ====================
    zip_file_path: Optional[str]
    readme_content: Optional[str]
    
    # ==================== METADATA ====================
    current_node: str
    error_message: Optional[str]
    is_complete: bool
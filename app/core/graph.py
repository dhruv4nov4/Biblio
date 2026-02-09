"""
LangGraph Workflow: Orchestrates the entire build pipeline with HITL checkpoints.
Connects all nodes in the correct sequence with conditional routing.

HITL (Human-in-the-Loop) Flow:
START → Gatekeeper → Architect → [PAUSE: Feature Approval] → [PAUSE: Tech Stack Approval] → Builder → Syntax Guard → Auditor → Packager → END
"""
from langgraph.graph import StateGraph, END
from app.models.state import BuilderState
from app.nodes.scope_gatekeeper import scope_gatekeeper_node, should_continue_after_gatekeeper
from app.nodes.architect import architect_node
from app.nodes.checkpoints import (
    feature_approval_checkpoint,
    techstack_approval_checkpoint,
    resume_after_feature_approval,
    resume_after_techstack_approval
)
from app.nodes.builder import builder_node
from app.nodes.syntax_guard import syntax_guard_node, should_retry_after_syntax
from app.nodes.auditor import auditor_node, should_retry_after_audit
from app.nodes.dependency_analyzer import dependency_analyzer_node
from app.nodes.packager import packager_node
from app.utils.logger import get_logger

logger = get_logger(__name__)


def create_builder_graph() -> StateGraph:
    """
    Create the complete LangGraph workflow with HITL checkpoints.
    
    Flow:
    START → Gatekeeper → Architect → Feature Checkpoint (PAUSE) → Tech Stack Checkpoint (PAUSE) → Builder → Syntax Guard → Auditor → Packager → END
    
    Checkpoint Edges:
    - Feature Checkpoint: Pauses for user to approve/modify features and design specs
    - Tech Stack Checkpoint: Pauses for user to approve/modify tech stack and file structure
    
    Conditional Edges:
    - Gatekeeper: If not feasible → END
    - Syntax Guard: If errors → retry Builder (max 2 times)
    - Auditor: If semantic issues → retry Builder (max 2 times)
    """
    
    # Initialize graph
    workflow = StateGraph(BuilderState)
    
    # Add all nodes
    workflow.add_node("gatekeeper", scope_gatekeeper_node)
    workflow.add_node("architect", architect_node)
    
    # HITL Checkpoint nodes
    workflow.add_node("feature_checkpoint", feature_approval_checkpoint)
    workflow.add_node("techstack_checkpoint", techstack_approval_checkpoint)
    
    # Execution nodes
    workflow.add_node("builder", builder_node)
    workflow.add_node("syntax_guard", syntax_guard_node)
    workflow.add_node("auditor", auditor_node)
    workflow.add_node("dependency_analyzer", dependency_analyzer_node)
    workflow.add_node("packager", packager_node)
    
    # Set entry point
    workflow.set_entry_point("gatekeeper")
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "gatekeeper",
        should_continue_after_gatekeeper,
        {
            "architect": "architect",
            "end": END
        }
    )
    
    # Architect → Feature Checkpoint (always pause for approval)
    workflow.add_edge("architect", "feature_checkpoint")
    
    # Feature Checkpoint → END (pauses here, pipeline resumes via API)
    # The checkpoint sets waiting_for_approval = True
    # Resume is handled by run_builder_pipeline_phase2
    workflow.add_edge("feature_checkpoint", END)
    
    # Tech Stack Checkpoint → END (pauses here, pipeline resumes via API)
    workflow.add_edge("techstack_checkpoint", END)
    
    # Builder → Syntax Guard
    workflow.add_edge("builder", "syntax_guard")
    
    # Conditional: Syntax Guard routes to Auditor (if issues) or Dependency Analyzer (if clean)
    workflow.add_conditional_edges(
        "syntax_guard",
        should_retry_after_syntax,
        {
            "auditor": "auditor",
            "dependency_analyzer": "dependency_analyzer"
        }
    )
    
    # Auditor (Code Fixer) → Dependency Analyzer (always, no retries)
    workflow.add_conditional_edges(
        "auditor",
        should_retry_after_audit,
        {
            "dependency_analyzer": "dependency_analyzer"
        }
    )
    
    # Dependency Analyzer → Packager → END
    workflow.add_edge("dependency_analyzer", "packager")
    workflow.add_edge("packager", END)
    
    return workflow.compile()


def create_phase2_graph() -> StateGraph:
    """
    Create Phase 2 graph: Tech Stack Checkpoint → Builder → ... → Packager
    This graph is used after feature approval to continue the pipeline.
    """
    workflow = StateGraph(BuilderState)
    
    workflow.add_node("techstack_checkpoint", techstack_approval_checkpoint)
    workflow.add_node("builder", builder_node)
    workflow.add_node("syntax_guard", syntax_guard_node)
    workflow.add_node("auditor", auditor_node)
    workflow.add_node("dependency_analyzer", dependency_analyzer_node)
    workflow.add_node("packager", packager_node)
    
    workflow.set_entry_point("techstack_checkpoint")
    
    # Tech Stack Checkpoint → END (pauses for approval)
    workflow.add_edge("techstack_checkpoint", END)
    
    # Builder flow (used after tech stack approval)
    workflow.add_edge("builder", "syntax_guard")
    
    workflow.add_conditional_edges(
        "syntax_guard",
        should_retry_after_syntax,
        {
            "auditor": "auditor",
            "dependency_analyzer": "dependency_analyzer"
        }
    )
    
    workflow.add_conditional_edges(
        "auditor",
        should_retry_after_audit,
        {
            "dependency_analyzer": "dependency_analyzer"
        }
    )
    
    workflow.add_edge("dependency_analyzer", "packager")
    workflow.add_edge("packager", END)
    
    return workflow.compile()


def create_phase3_graph() -> StateGraph:
    """
    Create Phase 3 graph: Builder → Syntax Guard → Auditor → Packager
    This graph is used after tech stack approval to generate code.
    """
    workflow = StateGraph(BuilderState)
    
    workflow.add_node("builder", builder_node)
    workflow.add_node("syntax_guard", syntax_guard_node)
    workflow.add_node("auditor", auditor_node)
    workflow.add_node("dependency_analyzer", dependency_analyzer_node)
    workflow.add_node("packager", packager_node)
    
    workflow.set_entry_point("builder")
    
    workflow.add_edge("builder", "syntax_guard")
    
    workflow.add_conditional_edges(
        "syntax_guard",
        should_retry_after_syntax,
        {
            "auditor": "auditor",
            "dependency_analyzer": "dependency_analyzer"
        }
    )
    
    workflow.add_conditional_edges(
        "auditor",
        should_retry_after_audit,
        {
            "dependency_analyzer": "dependency_analyzer"
        }
    )
    
    workflow.add_edge("dependency_analyzer", "packager")
    workflow.add_edge("packager", END)
    
    return workflow.compile()


# Global graph instances
builder_graph = create_builder_graph()
phase2_graph = create_phase2_graph()
phase3_graph = create_phase3_graph()


async def run_builder_pipeline(
    task_id: str,
    user_query: str,
    reference_url: str = None,
    callback=None
) -> BuilderState:
    """
    Execute Phase 1 of the build pipeline (up to Feature Approval checkpoint).
    
    Args:
        task_id: Unique identifier for this task
        user_query: User's project request
        reference_url: Optional URL to clone
        callback: Optional function for progress updates
    
    Returns:
        BuilderState paused at feature_approval_checkpoint
    """
    
    logger.info(f"[PIPELINE] Starting Phase 1 (Planning) for task: {task_id}")
    
    # Initialize state with HITL fields
    initial_state: BuilderState = {
        "task_id": task_id,
        "user_query": user_query,
        "reference_url": reference_url,
        "is_feasible": False,
        "classification": None,
        "refusal_reason": None,
        "tech_stack": None,
        "file_structure": [],
        "asset_manifest": [],
        "reasoning": None,
        "project_features": [],
        "design_specs": None,
        # HITL fields
        "approval_stage": None,
        "waiting_for_approval": False,
        "approved_features": [],
        "approved_design_specs": None,
        "approved_tech_stack": None,
        "approved_file_structure": [],
        "approved_asset_manifest": [],
        "user_requirements": None,
        # Execution fields
        "generated_code": {},
        # NEW: Validation fields (Syntax Guard - LLM-powered)
        "syntax_guard_validation": None,
        "validation_issues": [],
        "validation_passed": False,
        # NEW: Code fixing fields (Auditor - surgical fixes)
        "code_fixes_applied": [],
        "fix_summary": None,
        # Legacy validation fields
        "syntax_errors": [],
        "semantic_issues": [],
        "retry_count": 0,
        "zip_file_path": None,
        "readme_content": None,
        "current_node": "start",
        "error_message": None,
        "is_complete": False
    }
    
    # Execute Phase 1 graph
    try:
        final_state = None
        
        for state in builder_graph.stream(initial_state):
            for node_name, node_state in state.items():
                final_state = node_state
                
                if callback:
                    await callback({
                        "status": "processing",
                        "node": node_state.get("current_node", node_name),
                        "message": f"Processing: {node_name}",
                        "tech_stack": node_state.get("tech_stack"),
                        "file_structure": node_state.get("file_structure"),
                        "asset_manifest": node_state.get("asset_manifest"),
                        "reasoning": node_state.get("reasoning"),
                        "classification": node_state.get("classification"),
                        "project_features": node_state.get("project_features"),
                        "design_specs": node_state.get("design_specs"),
                        # HITL status
                        "approval_stage": node_state.get("approval_stage"),
                        "waiting_for_approval": node_state.get("waiting_for_approval"),
                    })
                
                logger.info(f"[PIPELINE] Completed node: {node_name}")
        
        if final_state and final_state.get("waiting_for_approval"):
            logger.info(f"[PIPELINE] Phase 1 complete. Waiting for feature approval.")
        
        return final_state
        
    except Exception as e:
        logger.error(f"[PIPELINE] Fatal error: {str(e)}")
        return {
            **initial_state,
            "error_message": str(e),
            "is_complete": True
        }


async def run_builder_pipeline_phase2(
    state: BuilderState,
    callback=None
) -> BuilderState:
    """
    Execute Phase 2 of the build pipeline (Tech Stack Approval).
    Called after user approves features.
    
    Args:
        state: Current BuilderState with approved features
        callback: Optional function for progress updates
    
    Returns:
        BuilderState paused at techstack_approval_checkpoint
    """
    
    logger.info(f"[PIPELINE] Starting Phase 2 (Tech Stack) for task: {state['task_id']}")
    
    try:
        final_state = None
        
        for step in phase2_graph.stream(state):
            for node_name, node_state in step.items():
                final_state = node_state
                
                if callback:
                    await callback({
                        "status": "processing",
                        "node": node_state.get("current_node", node_name),
                        "message": f"Processing: {node_name}",
                        "tech_stack": node_state.get("tech_stack"),
                        "file_structure": node_state.get("file_structure"),
                        "asset_manifest": node_state.get("asset_manifest"),
                        "approval_stage": node_state.get("approval_stage"),
                        "waiting_for_approval": node_state.get("waiting_for_approval"),
                    })
                
                logger.info(f"[PIPELINE] Completed node: {node_name}")
        
        if final_state and final_state.get("waiting_for_approval"):
            logger.info(f"[PIPELINE] Phase 2 complete. Waiting for tech stack approval.")
        
        return final_state
        
    except Exception as e:
        logger.error(f"[PIPELINE] Phase 2 error: {str(e)}")
        return {
            **state,
            "error_message": str(e),
            "is_complete": True
        }


async def run_builder_pipeline_phase3(
    state: BuilderState,
    callback=None
) -> BuilderState:
    """
    Execute Phase 3 of the build pipeline (Code Generation).
    Called after user approves tech stack.
    
    Args:
        state: Current BuilderState with all approvals
        callback: Optional function for progress updates
    
    Returns:
        Final BuilderState with generated code and ZIP file
    """
    
    logger.info(f"[PIPELINE] Starting Phase 3 (Building) for task: {state['task_id']}")
    
    # Update state to indicate building phase
    state["approval_stage"] = "building"
    state["waiting_for_approval"] = False
    
    try:
        final_state = None
        
        for step in phase3_graph.stream(state):
            for node_name, node_state in step.items():
                final_state = node_state
                
                if callback:
                    await callback({
                        "status": "processing",
                        "node": node_state.get("current_node", node_name),
                        "message": f"Processing: {node_name}",
                        "approval_stage": node_state.get("approval_stage"),
                        "waiting_for_approval": node_state.get("waiting_for_approval"),
                    })
                
                logger.info(f"[PIPELINE] Completed node: {node_name}")
        
        logger.info(f"[PIPELINE] Phase 3 complete. Build finished for task: {state['task_id']}")
        return final_state
        
    except Exception as e:
        logger.error(f"[PIPELINE] Phase 3 error: {str(e)}")
        return {
            **state,
            "error_message": str(e),
            "is_complete": True
        }
"""
HITL Checkpoint Nodes: Pause points in the pipeline for user approval.
These nodes set the waiting flag and allow the pipeline to be resumed
after user provides feedback/modifications.
"""
from app.models.state import BuilderState
from app.utils.logger import get_logger

logger = get_logger(__name__)


def feature_approval_checkpoint(state: BuilderState) -> BuilderState:
    """
    Checkpoint Node: Pause for Feature & Design Approval
    
    This node is reached after the Architect generates the initial blueprint.
    The pipeline pauses here, waiting for user to:
    - Review and approve/modify project features
    - Review and approve/modify design specifications
    - Add any additional requirements
    
    The pipeline resumes when the user calls the /approve-features endpoint.
    """
    logger.info("[CHECKPOINT] Pausing for Feature & Design Approval")
    
    state["current_node"] = "feature_approval_checkpoint"
    state["approval_stage"] = "feature_approval"
    state["waiting_for_approval"] = True
    
    # Initialize approved fields with architect's suggestions (user can modify)
    if not state.get("approved_features"):
        state["approved_features"] = state.get("project_features", [])
    if not state.get("approved_design_specs"):
        state["approved_design_specs"] = state.get("design_specs", {})
    
    logger.info(f"[CHECKPOINT] Features pending approval: {len(state.get('project_features', []))}")
    logger.info(f"[CHECKPOINT] Waiting for user input...")
    
    return state


def techstack_approval_checkpoint(state: BuilderState) -> BuilderState:
    """
    Checkpoint Node: Pause for Tech Stack Approval
    
    This node is reached after user approves features.
    The pipeline pauses here, waiting for user to:
    - Review and approve/modify tech stack choice
    - Review and approve/modify file structure
    - Review and approve/modify CDN dependencies
    
    The pipeline resumes when the user calls the /approve-techstack endpoint.
    """
    logger.info("[CHECKPOINT] Pausing for Tech Stack Approval")
    
    state["current_node"] = "techstack_approval_checkpoint"
    state["approval_stage"] = "techstack_approval"
    state["waiting_for_approval"] = True
    
    # Initialize approved fields with architect's suggestions (user can modify)
    if not state.get("approved_tech_stack"):
        state["approved_tech_stack"] = state.get("tech_stack")
    if not state.get("approved_file_structure"):
        state["approved_file_structure"] = state.get("file_structure", [])
    if not state.get("approved_asset_manifest"):
        state["approved_asset_manifest"] = state.get("asset_manifest", [])
    
    logger.info(f"[CHECKPOINT] Tech stack pending approval: {state.get('tech_stack')}")
    logger.info(f"[CHECKPOINT] Files pending approval: {len(state.get('file_structure', []))}")
    logger.info(f"[CHECKPOINT] Waiting for user input...")
    
    return state


def should_pause_for_feature_approval(state: BuilderState) -> str:
    """
    Router: Determine if we should pause for feature approval.
    Always pauses in HITL mode (default behavior).
    """
    # If already approved, skip checkpoint
    if state.get("approval_stage") == "features_approved":
        logger.info("[ROUTER] Features already approved, continuing...")
        return "techstack_checkpoint"
    
    # Default: pause for approval
    return "feature_checkpoint"


def should_pause_for_techstack_approval(state: BuilderState) -> str:
    """
    Router: Determine if we should pause for tech stack approval.
    Always pauses in HITL mode (default behavior).
    """
    # If already approved, skip checkpoint
    if state.get("approval_stage") == "techstack_approved":
        logger.info("[ROUTER] Tech stack already approved, continuing to builder...")
        return "builder"
    
    # Default: pause for approval
    return "techstack_checkpoint"


def resume_after_feature_approval(state: BuilderState) -> BuilderState:
    """
    Resume node: Called after user approves features.
    Updates state with user's modifications and continues pipeline.
    """
    logger.info("[CHECKPOINT] Resuming after feature approval")
    
    state["approval_stage"] = "features_approved"
    state["waiting_for_approval"] = False
    state["current_node"] = "feature_approved"
    
    # Log approved content
    approved_count = len(state.get("approved_features", []))
    core_count = len([f for f in state.get("approved_features", []) if f.get("priority") == "core"])
    enhancement_count = approved_count - core_count
    
    logger.info(f"[CHECKPOINT] User approved {approved_count} features ({core_count} core, {enhancement_count} enhancement)")
    
    return state


def resume_after_techstack_approval(state: BuilderState) -> BuilderState:
    """
    Resume node: Called after user approves tech stack.
    Updates state with user's modifications and continues to builder.
    """
    logger.info("[CHECKPOINT] Resuming after tech stack approval")
    
    state["approval_stage"] = "techstack_approved"
    state["waiting_for_approval"] = False
    state["current_node"] = "techstack_approved"
    
    # Log approved content
    logger.info(f"[CHECKPOINT] User approved tech stack: {state.get('approved_tech_stack')}")
    logger.info(f"[CHECKPOINT] User approved {len(state.get('approved_file_structure', []))} files")
    logger.info(f"[CHECKPOINT] User approved {len(state.get('approved_asset_manifest', []))} dependencies")
    
    if state.get("user_requirements"):
        logger.info(f"[CHECKPOINT] User added requirements: {state.get('user_requirements')[:100]}...")
    
    return state

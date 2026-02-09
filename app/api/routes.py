"""
FastAPI Routes: API endpoints for the AI Builder Platform with HITL Approval Workflow.
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uuid
import asyncio
import json
from app.core.graph import run_builder_pipeline, run_builder_pipeline_phase2, run_builder_pipeline_phase3
from app.nodes.architect import refine_file_structure
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


# ==================== Request/Response Models ====================

class BuildRequest(BaseModel):
    """Request model for build endpoint."""
    user_query: str
    reference_url: Optional[str] = None


class BuildResponse(BaseModel):
    """Response model for build initiation."""
    task_id: str
    message: str
    status: str


class FeatureApprovalRequest(BaseModel):
    """Request model for approving features and design specs."""
    approved_features: List[Dict[str, Any]]
    approved_design_specs: Dict[str, str]
    user_requirements: Optional[str] = None


class TechStackApprovalRequest(BaseModel):
    """Request model for approving tech stack."""
    approved_tech_stack: str
    approved_file_structure: List[Dict[str, Any]]
    approved_asset_manifest: List[Dict[str, Any]]
    user_requirements: Optional[str] = None


class GenerateStructureRequest(BaseModel):
    """Request to generate file structure from tech stack."""
    tech_stack: str


class GenerateStructureResponse(BaseModel):
    """Response with new file structure."""
    file_structure: List[Dict[str, Any]]
    message: str


class ApprovalResponse(BaseModel):
    """Response model for approval endpoints."""
    task_id: str
    message: str
    status: str
    next_stage: str


class BuildStatus(BaseModel):
    """Status check response."""
    task_id: str
    status: str
    current_node: Optional[str] = None
    error_message: Optional[str] = None
    zip_file_path: Optional[str] = None
    is_complete: bool
    # Blueprint data for tabbed UI
    tech_stack: Optional[str] = None
    file_structure: Optional[List[Dict[str, Any]]] = None
    asset_manifest: Optional[List[Dict[str, Any]]] = None
    reasoning: Optional[str] = None
    classification: Optional[str] = None
    # Feature planning data
    project_features: Optional[List[Dict[str, Any]]] = None
    design_specs: Optional[Dict[str, Any]] = None
    # HITL approval status
    approval_stage: Optional[str] = None
    waiting_for_approval: bool = False
    # User-approved content (for display)
    approved_features: Optional[List[Dict[str, Any]]] = None
    approved_design_specs: Optional[Dict[str, Any]] = None
    approved_tech_stack: Optional[str] = None


# ==================== In-Memory Task Storage ====================
# For production, use Redis or a proper database
active_tasks = {}


# ==================== Endpoints ====================

@router.post("/build", response_model=BuildResponse)
async def create_build(request: BuildRequest, background_tasks: BackgroundTasks):
    """
    Initiate a new build task (Phase 1: Planning).
    
    Returns task_id for polling status.
    Pipeline will pause at feature_approval_checkpoint for user approval.
    """
    task_id = str(uuid.uuid4())
    
    logger.info(f"[API] New build request: {task_id}")
    logger.info(f"[API] Query: {request.user_query[:100]}")
    
    # Store initial task state
    active_tasks[task_id] = {
        "status": "queued",
        "current_node": None,
        "error_message": None,
        "is_complete": False,
        "approval_stage": None,
        "waiting_for_approval": False,
        "state": None  # Store full state for resumption
    }
    
    # Start build in background
    background_tasks.add_task(
        execute_build_phase1,
        task_id,
        request.user_query,
        request.reference_url
    )
    
    return BuildResponse(
        task_id=task_id,
        message="Build started. Pipeline will pause for feature approval.",
        status="queued"
    )


async def execute_build_phase1(task_id: str, user_query: str, reference_url: str = None):
    """Background task to execute Phase 1 (up to feature approval)."""
    try:
        active_tasks[task_id]["status"] = "processing"
        
        async def progress_callback(update: dict):
            """Update active_tasks with latest state for real-time SSE updates."""
            current_task = active_tasks.get(task_id, {})
            active_tasks[task_id] = {
                **current_task,
                "status": update.get("status", "processing"),
                "current_node": update.get("node"),
                "tech_stack": update.get("tech_stack", current_task.get("tech_stack")),
                "file_structure": update.get("file_structure", current_task.get("file_structure")),
                "asset_manifest": update.get("asset_manifest", current_task.get("asset_manifest")),
                "reasoning": update.get("reasoning", current_task.get("reasoning")),
                "classification": update.get("classification", current_task.get("classification")),
                "project_features": update.get("project_features", current_task.get("project_features")),
                "design_specs": update.get("design_specs", current_task.get("design_specs")),
                "approval_stage": update.get("approval_stage", current_task.get("approval_stage")),
                "waiting_for_approval": update.get("waiting_for_approval", False),
            }
        
        # Run Phase 1 (up to feature approval checkpoint)
        final_state = await run_builder_pipeline(
            task_id=task_id,
            user_query=user_query,
            reference_url=reference_url,
            callback=progress_callback
        )
        
        # Update task state
        if final_state.get("waiting_for_approval"):
            # Paused for approval
            active_tasks[task_id].update({
                "status": "waiting_for_approval",
                "current_node": final_state.get("current_node"),
                "approval_stage": final_state.get("approval_stage"),
                "waiting_for_approval": True,
                "is_complete": False,
                "state": final_state,  # Store for resumption
                # Blueprint data
                "tech_stack": final_state.get("tech_stack"),
                "file_structure": final_state.get("file_structure"),
                "asset_manifest": final_state.get("asset_manifest"),
                "reasoning": final_state.get("reasoning"),
                "classification": final_state.get("classification"),
                "project_features": final_state.get("project_features"),
                "design_specs": final_state.get("design_specs"),
            })
            logger.info(f"[API] Build {task_id} paused for feature approval")
        elif final_state.get("is_complete"):
            # Completed or failed (e.g., rejected by gatekeeper)
            active_tasks[task_id].update({
                "status": "completed" if final_state.get("zip_file_path") else "failed",
                "current_node": final_state.get("current_node"),
                "error_message": final_state.get("error_message") or final_state.get("refusal_reason"),
                "is_complete": True,
                "state": final_state,
            })
            logger.info(f"[API] Build {task_id} completed in Phase 1")
        
    except Exception as e:
        logger.error(f"[API] Build {task_id} failed: {str(e)}")
        active_tasks[task_id] = {
            "status": "failed",
            "error_message": str(e),
            "is_complete": True
        }


@router.post("/build/{task_id}/approve-features", response_model=ApprovalResponse)
async def approve_features(task_id: str, request: FeatureApprovalRequest, background_tasks: BackgroundTasks):
    """
    Approve features and design specs, continue to tech stack approval.
    
    User can modify the features and design specs before approving.
    """
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task_data = active_tasks[task_id]
    
    if task_data.get("approval_stage") != "feature_approval":
        raise HTTPException(
            status_code=400, 
            detail=f"Task is not waiting for feature approval. Current stage: {task_data.get('approval_stage')}"
        )
    
    logger.info(f"[API] Feature approval received for task: {task_id}")
    logger.info(f"[API] Approved features: {len(request.approved_features)}")
    
    # Get current state
    state = task_data.get("state")
    if not state:
        raise HTTPException(status_code=400, detail="Task state not found")
    
    # Update state with user approvals
    state["approved_features"] = request.approved_features
    state["approved_design_specs"] = request.approved_design_specs
    if request.user_requirements:
        state["user_requirements"] = request.user_requirements
    state["approval_stage"] = "features_approved"
    state["waiting_for_approval"] = False
    
    # Update task data
    active_tasks[task_id].update({
        "status": "processing",
        "approval_stage": "transitioning_to_techstack",
        "waiting_for_approval": False,
        "approved_features": request.approved_features,
        "approved_design_specs": request.approved_design_specs,
        "state": state,
    })
    
    # Continue to Phase 2 in background
    background_tasks.add_task(execute_build_phase2, task_id, state)
    
    return ApprovalResponse(
        task_id=task_id,
        message="Features approved. Moving to tech stack approval.",
        status="processing",
        next_stage="techstack_approval"
    )


async def execute_build_phase2(task_id: str, state: dict):
    """Background task to execute Phase 2 (tech stack approval)."""
    try:
        async def progress_callback(update: dict):
            current_task = active_tasks.get(task_id, {})
            active_tasks[task_id] = {
                **current_task,
                "status": update.get("status", "processing"),
                "current_node": update.get("node"),
                "approval_stage": update.get("approval_stage"),
                "waiting_for_approval": update.get("waiting_for_approval", False),
            }
        
        # Run Phase 2 (tech stack checkpoint)
        final_state = await run_builder_pipeline_phase2(state, callback=progress_callback)
        
        if final_state.get("waiting_for_approval"):
            active_tasks[task_id].update({
                "status": "waiting_for_approval",
                "current_node": final_state.get("current_node"),
                "approval_stage": final_state.get("approval_stage"),
                "waiting_for_approval": True,
                "is_complete": False,
                "state": final_state,
                # Include approved content for display
                "approved_tech_stack": final_state.get("approved_tech_stack"),
                "approved_file_structure": final_state.get("approved_file_structure"),
                "approved_asset_manifest": final_state.get("approved_asset_manifest"),
            })
            logger.info(f"[API] Build {task_id} paused for tech stack approval")
            
    except Exception as e:
        logger.error(f"[API] Phase 2 failed for {task_id}: {str(e)}")
        active_tasks[task_id].update({
            "status": "failed",
            "error_message": str(e),
            "is_complete": True
        })


@router.post("/build/{task_id}/approve-techstack", response_model=ApprovalResponse)
async def approve_techstack(task_id: str, request: TechStackApprovalRequest, background_tasks: BackgroundTasks):
    """
    Approve tech stack and file structure, proceed to code generation.
    
    User can modify the tech stack, file structure, and dependencies before approving.
    """
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task_data = active_tasks[task_id]
    
    if task_data.get("approval_stage") != "techstack_approval":
        raise HTTPException(
            status_code=400, 
            detail=f"Task is not waiting for tech stack approval. Current stage: {task_data.get('approval_stage')}"
        )
    
    logger.info(f"[API] Tech stack approval received for task: {task_id}")
    logger.info(f"[API] Approved tech stack: {request.approved_tech_stack}")
    logger.info(f"[API] Approved files: {len(request.approved_file_structure)}")
    
    # Get current state
    state = task_data.get("state")
    if not state:
        raise HTTPException(status_code=400, detail="Task state not found")
    
    # Update state with user approvals
    state["approved_tech_stack"] = request.approved_tech_stack
    state["approved_file_structure"] = request.approved_file_structure
    state["approved_asset_manifest"] = request.approved_asset_manifest
    if request.user_requirements:
        # Append to existing requirements
        existing = state.get("user_requirements", "") or ""
        state["user_requirements"] = f"{existing}\n{request.user_requirements}".strip()
    state["approval_stage"] = "techstack_approved"
    state["waiting_for_approval"] = False
    
    # Update task data
    active_tasks[task_id].update({
        "status": "processing",
        "approval_stage": "building",
        "waiting_for_approval": False,
        "approved_tech_stack": request.approved_tech_stack,
        "state": state,
    })
    
    # Continue to Phase 3 (code generation) in background
    background_tasks.add_task(execute_build_phase3, task_id, state)
    
    return ApprovalResponse(
        task_id=task_id,
        message="Tech stack approved. Starting code generation with your approved specifications.",
        status="processing",
        next_stage="building"
    )


async def execute_build_phase3(task_id: str, state: dict):
    """Background task to execute Phase 3 (code generation)."""
    try:
        async def progress_callback(update: dict):
            current_task = active_tasks.get(task_id, {})
            active_tasks[task_id] = {
                **current_task,
                "status": update.get("status", "processing"),
                "current_node": update.get("node"),
                "approval_stage": "building",
                "waiting_for_approval": False,
            }
        
        # Run Phase 3 (code generation)
        final_state = await run_builder_pipeline_phase3(state, callback=progress_callback)
        
        # Update final status
        active_tasks[task_id].update({
            "status": "completed" if final_state.get("zip_file_path") else "failed",
            "current_node": final_state.get("current_node"),
            "error_message": final_state.get("error_message"),
            "zip_file_path": final_state.get("zip_file_path"),
            "is_complete": True,
            "state": final_state,
            "approval_stage": "completed",
        })
        
        logger.info(f"[API] Build {task_id} completed successfully")
        
    except Exception as e:
        logger.error(f"[API] Phase 3 failed for {task_id}: {str(e)}")
        active_tasks[task_id].update({
            "status": "failed",
            "error_message": str(e),
            "is_complete": True
        })


@router.post("/build/{task_id}/generate-structure", response_model=GenerateStructureResponse)
async def generate_structure(task_id: str, request: GenerateStructureRequest):
    """
    Generate a new file structure based on user-provided tech stack.
    """
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task_data = active_tasks[task_id]
    
    # Get project context from state
    state = task_data.get("state", {})
    user_query = state.get("user_query")
    project_features = state.get("approved_features") or state.get("project_features", [])
    
    if not user_query:
        raise HTTPException(status_code=400, detail="User query not found in task state")
        
    logger.info(f"[API] Generating structure for task {task_id} with stack: {request.tech_stack}")
    
    # Generate new structure
    new_structure = refine_file_structure(user_query, project_features, request.tech_stack)
    
    if not new_structure:
        raise HTTPException(status_code=500, detail="Failed to generate file structure")
        
    return GenerateStructureResponse(
        file_structure=new_structure,
        message="File structure updated successfully"
    )


@router.get("/build/{task_id}/status", response_model=BuildStatus)
async def get_build_status(task_id: str):
    """Check the status of a build task."""
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task_data = active_tasks[task_id]
    
    return BuildStatus(
        task_id=task_id,
        status=task_data.get("status", "unknown"),
        current_node=task_data.get("current_node"),
        error_message=task_data.get("error_message"),
        zip_file_path=task_data.get("zip_file_path"),
        is_complete=task_data.get("is_complete", False),
        # Blueprint data
        tech_stack=task_data.get("tech_stack"),
        file_structure=task_data.get("file_structure"),
        asset_manifest=task_data.get("asset_manifest"),
        reasoning=task_data.get("reasoning"),
        classification=task_data.get("classification"),
        # Feature planning data
        project_features=task_data.get("project_features"),
        design_specs=task_data.get("design_specs"),
        # HITL approval status
        approval_stage=task_data.get("approval_stage"),
        waiting_for_approval=task_data.get("waiting_for_approval", False),
        # User-approved content
        approved_features=task_data.get("approved_features"),
        approved_design_specs=task_data.get("approved_design_specs"),
        approved_tech_stack=task_data.get("approved_tech_stack"),
    )


@router.get("/build/{task_id}/download")
async def download_build(task_id: str):
    """Download the generated ZIP file."""
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task_data = active_tasks[task_id]
    
    if not task_data.get("zip_file_path"):
        raise HTTPException(status_code=400, detail="Build not completed or failed")
    
    zip_path = task_data["zip_file_path"]
    
    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=f"project_{task_id}.zip"
    )


@router.get("/build/{task_id}/stream")
async def stream_build_progress(task_id: str):
    """Server-Sent Events endpoint for real-time progress updates."""
    async def event_generator():
        while True:
            if task_id not in active_tasks:
                yield f"data: {json.dumps({'error': 'Task not found'})}\n\n"
                break
            
            task_data = active_tasks[task_id]
            
            # Send current status with all data
            event_data = {
                'status': task_data.get('status', 'unknown'),
                'node': task_data.get('current_node'),
                'is_complete': task_data.get('is_complete', False),
                # Blueprint data
                'tech_stack': task_data.get('tech_stack'),
                'file_structure': task_data.get('file_structure'),
                'asset_manifest': task_data.get('asset_manifest'),
                'reasoning': task_data.get('reasoning'),
                'classification': task_data.get('classification'),
                'error_message': task_data.get('error_message'),
                # Feature planning data
                'project_features': task_data.get('project_features'),
                'design_specs': task_data.get('design_specs'),
                # HITL approval status
                'approval_stage': task_data.get('approval_stage'),
                'waiting_for_approval': task_data.get('waiting_for_approval', False),
                # User-approved content
                'approved_features': task_data.get('approved_features'),
                'approved_design_specs': task_data.get('approved_design_specs'),
                'approved_tech_stack': task_data.get('approved_tech_stack'),
            }
            yield f"data: {json.dumps(event_data)}\n\n"
            
            # If complete or waiting for approval, we can end the stream
            # (but for approval, we might want to keep it open for the UI)
            if task_data.get('is_complete'):
                break
            
            # Poll every second
            await asyncio.sleep(1)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "AI Builder Platform", "hitl_enabled": True}
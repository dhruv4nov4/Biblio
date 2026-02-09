"""
Node 3: The Builder
Generates actual executable code based on the Architect's blueprint AND USER APPROVALS.
Uses user-approved features, design specs, and tech stack for maximum accuracy.
"""
import time
from app.models.state import BuilderState
from app.core.llm_factory import llm_factory
from app.prompts.builder_prompts import build_code_generation_prompt
from app.utils.logger import get_logger
from app.config import settings

logger = get_logger(__name__)


def builder_node(state: BuilderState) -> BuilderState:
    """
    Node 3: Generate code for each file using USER-APPROVED specifications.
    
    HITL Enhancement:
    - Uses approved_features instead of project_features
    - Uses approved_design_specs instead of design_specs
    - Uses approved_tech_stack and approved_file_structure
    - Passes user_requirements to the prompt
    
    This ensures the generated code matches EXACTLY what the user approved.
    """
    
    # Determine which file structure to use (approved takes priority)
    file_structure = state.get("approved_file_structure") or state.get("file_structure", [])
    asset_manifest = state.get("approved_asset_manifest") or state.get("asset_manifest", [])
    
    logger.info(f"[BUILDER] Generating code for {len(file_structure)} files")
    logger.info(f"[BUILDER] Using USER-APPROVED specifications for maximum accuracy")
    
    state["current_node"] = "builder"
    
    # Log what we're using
    approved_features = state.get("approved_features", [])
    core_features = [f for f in approved_features if f.get("priority") == "core"]
    enhancement_features = [f for f in approved_features if f.get("priority") == "enhancement"]
    
    logger.info(f"[BUILDER] Approved features: {len(core_features)} core, {len(enhancement_features)} enhancement")
    logger.info(f"[BUILDER] Approved tech stack: {state.get('approved_tech_stack')}")
    
    if state.get("user_requirements"):
        logger.info(f"[BUILDER] User requirements: {state.get('user_requirements')[:100]}...")
    
    try:
        llm = llm_factory.get_builder_llm()
        
        # CRITICAL OPTIMIZATION: On retry, only regenerate files with errors
        files_to_generate = file_structure
        
        if state["retry_count"] > 0 and state["syntax_errors"]:
            # Extract filenames from error messages (format: "filename: error")
            error_filenames = set()
            for error in state["syntax_errors"]:
                if ":" in error:
                    filename = error.split(":")[0].strip()
                    error_filenames.add(filename)
            
            # Filter to only files with errors
            files_to_generate = [
                f for f in file_structure 
                if f["name"] in error_filenames
            ]
            
            logger.info(f"[BUILDER] RETRY MODE: Regenerating ONLY {len(files_to_generate)} files with errors")
            logger.info(f"[BUILDER] Error files: {list(error_filenames)}")
            logger.info(f"[BUILDER] Skipping {len(file_structure) - len(files_to_generate)} files that passed validation")
        
        for idx, file_spec in enumerate(files_to_generate):
            filename = file_spec["name"]
            logger.info(f"[BUILDER] Generating {filename} ({idx + 1}/{len(files_to_generate)})")
            
            # Build prompt with ALL user-approved content for accuracy
            prompt = build_code_generation_prompt(
                file_spec=file_spec,
                asset_manifest=asset_manifest,
                user_query=state["user_query"],
                # Original architect suggestions (fallback)
                project_features=state.get("project_features", []),
                design_specs=state.get("design_specs", {}),
                # HITL: User-approved content (takes priority)
                approved_features=state.get("approved_features"),
                approved_design_specs=state.get("approved_design_specs"),
                approved_tech_stack=state.get("approved_tech_stack"),
                approved_file_structure=file_structure, # Pass full structure context
                user_requirements=state.get("user_requirements"),
                # Retry context
                syntax_errors=state["syntax_errors"] if state["retry_count"] > 0 else None
            )
            
            # Generate code using Groq
            response = llm.invoke(prompt)
            code = response.content
            
            # Clean up any markdown artifacts
            code = code.strip()
            if code.startswith("```"):
                lines = code.split("\n")
                # Remove first line (```html, ```css, etc.)
                if lines[0].startswith("```"):
                    lines = lines[1:]
                # Remove last line if it's just ```
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                code = "\n".join(lines)
            
            state["generated_code"][filename] = code
            
            logger.info(f"[BUILDER] Generated {filename} ({len(code)} characters)")
            
            # Rate limiting: cooldown between files
            if idx < len(files_to_generate) - 1:
                time.sleep(settings.BUILDER_COOLDOWN_SECONDS)
        
        logger.info(f"[BUILDER] Successfully generated {len(files_to_generate)} files")
        
        # Calculate token savings on retry
        if state["retry_count"] > 0:
            skipped_files = len(file_structure) - len(files_to_generate)
            if skipped_files > 0:
                logger.info(f"[BUILDER] 💰 Token savings: Skipped {skipped_files} files on retry")
        
        return state
        
    except Exception as e:
        logger.error(f"[BUILDER] Error: {str(e)}")
        state["error_message"] = f"Code generation failed: {str(e)}"
        state["is_complete"] = True
        return state
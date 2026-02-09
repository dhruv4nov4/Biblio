"""
Node 2: The Architect
Creates the blueprint - file structure, tech stack, asset manifest, and feature planning.
"""
from app.models.state import BuilderState
from app.core.llm_factory import llm_factory
from app.prompts.architect_prompts import build_architect_prompt
from app.prompts.structure_prompts import build_structure_refinement_prompt
from app.utils.logger import get_logger
from app.utils.parsers import parse_llm_json, validate_json_schema

logger = get_logger(__name__)


def architect_node(state: BuilderState) -> BuilderState:
    """
    Node 2: Generate the project blueprint with feature planning.
    
    Output:
    - project_features: List of features with priorities and benefits
    - design_specs: Visual design specifications
    - tech_stack: The framework/approach to use
    - file_structure: List of files with generation prompts
    - asset_manifest: External dependencies (CDN links)
    """
    logger.info("[ARCHITECT] Designing project blueprint with feature planning")
    
    state["current_node"] = "architect"
    
    try:
        llm = llm_factory.get_architect_llm()
        prompt = build_architect_prompt(
            state["user_query"],
            state.get("reference_url")
        )
        
        response = llm.invoke(prompt)
        
        # FIX: Use robust JSON parser
        blueprint = parse_llm_json(response.content)
        
        # Validate required fields
        required_keys = ["tech_stack", "file_structure"]
        if not validate_json_schema(blueprint, required_keys):
            raise ValueError("Missing required fields in architect response")
        
        # Core blueprint fields
        state["tech_stack"] = blueprint["tech_stack"]
        state["file_structure"] = blueprint["file_structure"]
        state["asset_manifest"] = blueprint.get("asset_manifest", [])
        state["reasoning"] = blueprint.get("reasoning", "")
        
        # Feature planning fields (new)
        state["project_features"] = blueprint.get("project_features", [])
        state["design_specs"] = blueprint.get("design_specs", {})
        
        # Log comprehensive blueprint output
        logger.info(f"[ARCHITECT] Blueprint created:")
        logger.info(f"  - Tech Stack: {state['tech_stack']}")
        logger.info(f"  - Files: {len(state['file_structure'])}")
        logger.info(f"  - Assets: {len(state['asset_manifest'])}")
        logger.info(f"  - Features: {len(state['project_features'])}")
        
        # Log feature breakdown for visibility
        if state["project_features"]:
            core_features = [f for f in state["project_features"] if f.get("priority") == "core"]
            enhancement_features = [f for f in state["project_features"] if f.get("priority") == "enhancement"]
            logger.info(f"  - Core Features: {len(core_features)}")
            logger.info(f"  - Enhancement Features: {len(enhancement_features)}")
            
            for feature in state["project_features"]:
                logger.info(f"    [{feature.get('priority', 'unknown').upper()}] {feature.get('name', 'Unnamed')}")
        
        # Log design specs
        if state["design_specs"]:
            logger.info(f"  - Design Specs:")
            for key, value in state["design_specs"].items():
                logger.info(f"    {key}: {value[:50]}..." if len(str(value)) > 50 else f"    {key}: {value}")
        
        # Initialize code storage
        state["generated_code"] = {}
        state["syntax_errors"] = []
        state["semantic_issues"] = []
        state["retry_count"] = 0
        
        return state
        
    except Exception as e:
        logger.error(f"[ARCHITECT] Error: {str(e)}")
        state["error_message"] = f"Blueprint generation failed: {str(e)}"
        state["is_complete"] = True
        return state


def refine_file_structure(user_query: str, project_features: list, tech_stack: str):
    """
    Helper function to regenerate file structure based on new tech stack.
    Used by the API endpoint directly.
    """
    logger.info(f"[ARCHITECT] Refining structure for stack: {tech_stack}")
    
    try:
        llm = llm_factory.get_architect_llm()
        prompt = build_structure_refinement_prompt(
            user_query,
            project_features,
            tech_stack
        )
        
        response = llm.invoke(prompt)
        result = parse_llm_json(response.content)
        
        return result.get("file_structure", [])
        
    except Exception as e:
        logger.error(f"[ARCHITECT] Refinement failed: {str(e)}")
        return []
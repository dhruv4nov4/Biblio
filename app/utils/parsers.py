"""
Robust parsers for handling LLM outputs.
Critical utility to handle markdown-wrapped JSON from LLMs.
"""
import json
import re
from typing import Dict, Any
from app.utils.logger import get_logger

logger = get_logger(__name__)


def parse_llm_json(content: str) -> Dict[Any, Any]:
    """
    Reliably extract JSON from LLM markdown output.
    
    Handles common LLM quirks:
    - Markdown code blocks: ```json ... ```
    - Extra whitespace and newlines
    - Preamble text before JSON
    - Trailing explanations after JSON
    
    Args:
        content: Raw LLM response string
        
    Returns:
        Parsed dictionary
        
    Raises:
        json.JSONDecodeError: If no valid JSON found after cleanup
    """
    original_content = content
    
    try:
        # Step 1: Remove markdown code blocks
        content = re.sub(r'```json\s*', '', content, flags=re.IGNORECASE)
        content = re.sub(r'```\s*', '', content)
        
        # Step 2: Try to extract JSON object/array using regex
        # Look for content between outermost { } or [ ]
        json_match = re.search(r'(\{.*\}|\[.*\])', content, re.DOTALL)
        
        if json_match:
            content = json_match.group(1)
        
        # Step 3: Clean up whitespace
        content = content.strip()
        
        # Step 4: Parse JSON
        parsed = json.loads(content)
        
        logger.debug(f"[PARSER] Successfully parsed JSON from LLM output")
        return parsed
        
    except json.JSONDecodeError as e:
        logger.error(f"[PARSER] Failed to parse JSON. Original content: {original_content[:500]}")
        logger.error(f"[PARSER] Cleaned content: {content[:500]}")
        logger.error(f"[PARSER] Error: {str(e)}")
        
        # Last resort: try to extract JSON with better matching
        try:
            logger.warning("[PARSER] Attempting fallback extraction strategies...")
            
            # Strategy 1: Find balanced braces for complete objects
            brace_count = 0
            start_idx = content.find('{')
            if start_idx != -1:
                for i, char in enumerate(content[start_idx:], start=start_idx):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            # Found complete JSON object
                            potential_json = content[start_idx:i+1]
                            try:
                                parsed = json.loads(potential_json)
                                logger.warning("[PARSER] Used balanced brace extraction")
                                return parsed
                            except:
                                pass
            
            # Strategy 2: Try simple regex patterns
            objects = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
            for obj in objects:
                try:
                    parsed = json.loads(obj)
                    logger.warning("[PARSER] Used fallback regex extraction")
                    return parsed
                except:
                    continue
                    
        except Exception as fallback_error:
            logger.error(f"[PARSER] Fallback extraction also failed: {str(fallback_error)}")
        
        # If all else fails, return empty structure to prevent crashes
        logger.error("[PARSER] Returning empty fallback structure")
        return {
            "fixes_applied": [],
            "fixed_code": {},
            "summary": {
                "total_issues_fixed": 0,
                "files_modified": [],
                "files_unchanged": [],
                "all_issues_resolved": False,
                "error": "JSON parsing failed - LLM response was truncated or malformed"
            }
        }


def validate_json_schema(data: dict, required_keys: list) -> bool:
    """
    Validate that parsed JSON contains required keys.
    
    Args:
        data: Parsed JSON dictionary
        required_keys: List of required key names
        
    Returns:
        True if all required keys present, False otherwise
    """
    missing_keys = [key for key in required_keys if key not in data]
    
    if missing_keys:
        logger.warning(f"[PARSER] Missing required keys: {missing_keys}")
        return False
    
    return True
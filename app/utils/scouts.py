"""
Scouts: Metadata Extractors for the "Wiring Inspector" Architecture.

These lightweight parsers extract "wiring" metadata (IDs, routes, imports) 
from source code without reading the entire file content.
"""
import re
import ast
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Set
from app.utils.logger import get_logger

logger = get_logger(__name__)


class BaseScout:
    """Base class for all file scouts."""
    def inspect(self, content: str) -> Dict[str, Any]:
        """Inspect file content and return metadata."""
        raise NotImplementedError


class HTMLScout(BaseScout):
    """Extracts IDs, Classes, and script/link references from HTML."""
    
    def inspect(self, content: str) -> Dict[str, Any]:
        metadata = {
            "defined_ids": [],
            "defined_classes": [],
            "scripts": [],
            "links": []
        }
        
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract IDs
            for element in soup.find_all(id=True):
                metadata["defined_ids"].append(element['id'])
                
            # Extract Classes
            classes = set()
            for element in soup.find_all(class_=True):
                classes.update(element['class'])
            metadata["defined_classes"] = list(classes)
            
            # Extract Scripts
            for script in soup.find_all('script', src=True):
                metadata["scripts"].append(script['src'])
                
            # Extract Links (CSS)
            for link in soup.find_all('link', href=True):
                metadata["links"].append(link['href'])
                
        except Exception as e:
            logger.warning(f"[HTML SCOUT] Parsing failed: {e}")
            # Fallback to simple regex if BeautifulSoup fails
            metadata["defined_ids"] = re.findall(r'id=["\']([^"\']+)["\']', content)
            
        return metadata


class JSScout(BaseScout):
    """Extracts DOM selectors, API calls, and imports from JavaScript/TypeScript."""
    
    def inspect(self, content: str) -> Dict[str, Any]:
        metadata = {
            "dom_selectors": [],
            "api_calls": [],
            "imports": [],
            "exports": []
        }
        
        # 1. DOM Selectors (document.getElementById, querySelector, etc.)
        # Matches: getElementById('id') or "id"
        id_matches = re.findall(r"getElementById\(['\"]([^'\"]+)['\"]\)", content)
        # Matches: querySelector('#id') or '.class'
        qs_matches = re.findall(r"querySelector\(['\"]([^'\"]+)['\"]\)", content)
        metadata["dom_selectors"] = list(set(id_matches + qs_matches))
        
        # 2. API Calls (fetch, axios.get, etc.)
        # Matches: fetch('/api/...')
        fetch_matches = re.findall(r"fetch\(['\"]([^'\"]+)['\"]", content)
        # Matches: axios.get('/api/...')
        axios_matches = re.findall(r"axios\.[a-z]+\(['\"]([^'\"]+)['\"]", content)
        metadata["api_calls"] = list(set(fetch_matches + axios_matches))
        
        # 3. Imports and Requires
        # Matches: import ... from 'module'
        import_matches = re.findall(r"from ['\"]([^'\"]+)['\"]", content)
        # Matches: require('module')
        require_matches = re.findall(r"require\(['\"]([^'\"]+)['\"]\)", content)
        metadata["imports"] = list(set(import_matches + require_matches))
        
        return metadata


class PythonScout(BaseScout):
    """Extracts Imports, Classes, Functions, and Flask/FastAPI routes."""
    
    def inspect(self, content: str) -> Dict[str, Any]:
        metadata = {
            "imports": [],
            "defined_classes": [],
            "defined_functions": [],
            "api_routes": []
        }
        
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                # Imports
                if isinstance(node, ast.Import):
                    for name in node.names:
                        metadata["imports"].append(name.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        metadata["imports"].append(node.module)
                        
                # Classes
                elif isinstance(node, ast.ClassDef):
                    metadata["defined_classes"].append(node.name)
                    
                # Functions
                elif isinstance(node, ast.FunctionDef):
                    metadata["defined_functions"].append(node.name)
                    
                    # Detect Routes (Decorators)
                    # Looks for @app.route('/path') or @router.get('/path')
                    for decorator in node.decorator_list:
                        if isinstance(decorator, ast.Call):
                            # Check if it's a route call
                            if self._is_route_decorator(decorator):
                                route_path = self._extract_route_path(decorator)
                                if route_path:
                                    metadata["api_routes"].append(route_path)
                                    
        except SyntaxError:
            metadata["syntax_error"] = True
            logger.warning("[PYTHON SCOUT] Syntax Error detected during AST parsing")
        except Exception as e:
            logger.warning(f"[PYTHON SCOUT] Parsing failed: {e}")
            
        return metadata
    
    def _is_route_decorator(self, node: ast.Call) -> bool:
        """Heuristic to check if a decorator is likely a route definition."""
        try:
            # Case 1: @app.route(...)
            if isinstance(node.func, ast.Attribute) and node.func.attr in ['route', 'get', 'post', 'put', 'delete']:
                return True
            return False
        except:
            return False

    def _extract_route_path(self, node: ast.Call) -> str | None:
        """Extracts the string path from a route decorator."""
        try:
            if node.args and isinstance(node.args[0], ast.Constant):
                return node.args[0].value # Python 3.8+
            elif node.args and isinstance(node.args[0], ast.Str):
                return node.args[0].s # Older Python
            return None
        except:
            return None


class ProjectRegistry:
    """Orchestrator that builds the 'Wiring Diagram' for the project."""
    
    def __init__(self):
        self.scouts = {
            "html": HTMLScout(),
            "js": JSScout(),
            "ts": JSScout(),
            "jsx": JSScout(),
            "tsx": JSScout(),
            "py": PythonScout()
        }
        
    def build_wiring_diagram(self, generated_code: Dict[str, str]) -> Dict[str, Any]:
        """Scans all files and builds a comprehensive metadata map."""
        wiring_diagram = {}
        
        for filename, content in generated_code.items():
            ext = filename.split('.')[-1].lower()
            scout = self.scouts.get(ext)
            
            if scout:
                try:
                    logger.info(f"[SCOUT] Inspecting {filename}...")
                    metadata = scout.inspect(content)
                    wiring_diagram[filename] = metadata
                except Exception as e:
                    logger.error(f"[SCOUT] Failed to inspect {filename}: {e}")
                    wiring_diagram[filename] = {"error": str(e)}
            else:
                wiring_diagram[filename] = {"info": "No specialized scout for this file type"}
                
        return wiring_diagram

# Singleton instance
project_registry = ProjectRegistry()

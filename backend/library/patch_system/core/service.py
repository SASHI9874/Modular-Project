from typing import Dict, Any
from .generator import PatchGenerator
from .validator import PatchValidator
from .errors import PatchGenerationError, PatchValidationError, PatchApplyError


class PatchSystemService:
    """Patch system service"""
    
    def __init__(self):
        self.generator = PatchGenerator()
        self.validator = PatchValidator()
    
    def generate_patch(self, file_path: str, old_content: str, new_content: str) -> str:
        """Generate patch"""
        try:
            return self.generator.generate(file_path, old_content, new_content)
        except Exception as e:
            raise PatchGenerationError(f"Failed to generate patch: {e}")
    
    def validate_patch(self, patch: str, file_path: str) -> Dict[str, Any]:
        """Validate patch"""
        try:
            return self.validator.validate(patch, file_path)
        except Exception as e:
            raise PatchValidationError(f"Failed to validate patch: {e}")
    
    def apply_patch(self, patch: str, file_path: str) -> str:
        """Apply patch (placeholder - actual implementation in downloaded app)"""
        print(f"📌 [PatchSys] Apply patch to: {file_path}")
        
        validation = self.validate_patch(patch, file_path)
        
        if not validation['safe']:
            issues = ', '.join(validation['issues'])
            raise PatchApplyError(f"Unsafe patch: {issues}")
        
        # In real app, would apply using patch command or manual merge
        return f"Patch validated. Ready to apply to {file_path}"
    
    def plan_multi_file(self, task_description: str) -> Dict[str, Any]:
        """Plan multi-file edits"""
        print(f"📋 [PatchSys] Planning: {task_description}")
        
        # Simple planning - in real implementation, would use LLM
        plan = {
            "task": task_description,
            "files": [],
            "steps": [
                "1. Analyze codebase",
                "2. Identify files to modify",
                "3. Generate patches",
                "4. Validate changes"
            ]
        }
        
        return plan
    
    def execute(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Execute operation"""
        operations = {
            'generate': lambda: {
                "result": self.generate_patch(
                    kwargs.get('file_path', ''),
                    kwargs.get('old_content', ''),
                    kwargs.get('new_content', '')
                ),
                "success": True
            },
            'validate': lambda: {
                **self.validate_patch(
                    kwargs.get('patch', ''),
                    kwargs.get('file_path', '')
                ),
                "success": True
            },
            'apply': lambda: {
                "result": self.apply_patch(
                    kwargs.get('patch', ''),
                    kwargs.get('file_path', '')
                ),
                "success": True
            },
            'plan_multi': lambda: {
                **self.plan_multi_file(kwargs.get('task_description', '')),
                "success": True
            }
        }
        
        if operation not in operations:
            return {"result": f"Unknown operation: {operation}", "success": False}
        
        try:
            return operations[operation]()
        except Exception as e:
            print(f"❌ [PatchSys] Error: {e}")
            return {"result": str(e), "success": False, "error": str(e)}
import re
from typing import Dict, Any


class PatchValidator:
    """Validate patch safety"""
    
    @staticmethod
    def validate(patch: str, file_path: str) -> Dict[str, Any]:
        """Validate patch is safe to apply"""
        print(f"[PatchVal] Validating patch for: {file_path}")
        
        issues = []
        
        # Check for dangerous patterns
        dangerous = [
            (r'rm -rf', 'Dangerous delete command'),
            (r'DROP TABLE', 'SQL drop table'),
            (r'DELETE FROM.*WHERE 1=1', 'Dangerous SQL delete'),
            (r'eval\(', 'Eval usage'),
            (r'exec\(', 'Exec usage')
        ]
        
        for pattern, reason in dangerous:
            if re.search(pattern, patch, re.IGNORECASE):
                issues.append(f"  {reason}")
        
        # Check patch format
        if not patch.startswith('---'):
            issues.append("Invalid unified diff format")
        
        is_safe = len(issues) == 0
        
        if is_safe:
            print(f" [PatchVal] Patch is safe")
        else:
            print(f"  [PatchVal] Found {len(issues)} issues")
        
        return {
            "safe": is_safe,
            "issues": issues
        }
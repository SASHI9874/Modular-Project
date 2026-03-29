import difflib
from typing import List


class PatchGenerator:
    """Generate unified diffs"""
    
    @staticmethod
    def generate(file_path: str, old_content: str, new_content: str) -> str:
        """Generate unified diff patch"""
        print(f"📝 [PatchGen] Generating patch for: {file_path}")
        
        old_lines = old_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
            lineterm=''
        )
        
        patch = '\n'.join(diff)
        
        if not patch:
            return "No changes detected"
        
        print(f" [PatchGen] Generated {len(patch)} chars")
        return patch
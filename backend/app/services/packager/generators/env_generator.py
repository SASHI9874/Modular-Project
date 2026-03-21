import os
from typing import Dict, List
from app.services.library_service import library_service
from ..errors.packager_errors import CodeGenerationError


class EnvGenerator:
    """Generates .env files"""
    
    def generate(self, feature_keys: List[str]) -> Dict[str, str]:
        """
        Generate .env and .env.template files
        Returns dict: {filepath: content}
        """
        print(" [EnvGen] Generating environment files...")
        
        try:
            env_vars = self._collect_env_vars(feature_keys)
            
            files = {
                'backend/.env.template': self._generate_template(env_vars),
                'backend/.env': self._generate_defaults(env_vars)
            }
            
            print(f" [EnvGen] Generated {len(files)} env files")
            return files
        
        except Exception as e:
            print(f" [EnvGen] Error: {e}")
            raise CodeGenerationError(f"Env generation failed: {e}")
    
    def _collect_env_vars(self, feature_keys: List[str]) -> Dict[str, Dict]:
        """Collect env variables from all features"""
        env_groups = {}
        
        for key in feature_keys:
            manifest = library_service.get_feature(key)
            if not manifest or not manifest.config.env:
                continue
            
            category = manifest.ui.category or "General"
            
            if category not in env_groups:
                env_groups[category] = []
            
            for env_key, field in manifest.config.env.items():
                env_groups[category].append({
                    'key': env_key,
                    'default': str(field.default) if field.default else '',
                    'description': field.description or '',
                    'required': field.required if hasattr(field, 'required') else False,
                    'feature': manifest.name
                })
        
        return env_groups
    
    def _generate_template(self, env_groups: Dict) -> str:
        """Generate .env.template"""
        lines = ["# Environment Variables Template\n"]
        
        for category, vars in env_groups.items():
            lines.append(f"\n# === {category} ===")
            for var in vars:
                desc = f"# {var['description']}" if var['description'] else f"# Required by: {var['feature']}"
                lines.append(desc)
                lines.append(f"{var['key']}=")
        
        return "\n".join(lines)
    
    def _generate_defaults(self, env_groups: Dict) -> str:
        """Generate .env with defaults"""
        lines = ["# Environment Variables (with defaults)\n"]
        
        for category, vars in env_groups.items():
            lines.append(f"\n# === {category} ===")
            for var in vars:
                lines.append(f"{var['key']}={var['default']}")
        
        return "\n".join(lines)
from typing import Dict, List
from app.services.library_service import library_service
from ..errors.packager_errors import CodeGenerationError


class DocsGenerator:
    """Generates LLM-powered documentation"""
    
    def __init__(self, project_name: str):
        self.project_name = project_name
    
    def generate_readme(
        self, 
        feature_keys: List[str], 
        execution_mode: str, 
        frontend_mode: str,
        has_docker: bool = True,
        use_llm: bool = True
    ) -> str:
        """
        Generate README using LLM
        
        Args:
            use_llm: If True, uses LLM. If False, uses template (fallback)
        """
        print(" [DocsGen] Generating README...")
        
        try:
            # Collect feature data
            features_data = self._collect_feature_metadata(feature_keys)
            
            if use_llm:
                # Use LLM to generate
                readme = self._generate_with_llm(
                    features_data,
                    execution_mode,
                    frontend_mode,
                    has_docker
                )
            else:
                # Fallback to template
                readme = self._generate_template(
                    features_data,
                    execution_mode,
                    frontend_mode,
                    has_docker
                )
            
            print("✅ [DocsGen] README generated")
            return readme
        
        except Exception as e:
            print(f"⚠️  [DocsGen] LLM generation failed: {e}")
            print("   Falling back to template generation...")
            # Fallback
            features_data = self._collect_feature_metadata(feature_keys)
            return self._generate_template(features_data, execution_mode, frontend_mode, has_docker)
    
    def _collect_feature_metadata(self, feature_keys: List[str]) -> Dict:
        """Collect complete feature information for LLM"""
        data = {
            'project_name': self.project_name,
            'features': [],
            'env_vars': [],
            'api_endpoints': [],
            'capabilities': {
                'has_agent': False,
                'has_tools': False,
                'has_llm': False,
                'has_vector_db': False,
                'has_memory': False
            }
        }
        
        for key in feature_keys:
            manifest = library_service.get_feature(key)
            if not manifest:
                continue
            
            feature_info = {
                'name': manifest.name,
                'description': manifest.description,
                'category': manifest.ui.category or 'General',
                'capability': manifest.classification.capability,
                'key': key
            }
            
            # API endpoints
            if manifest.api and manifest.api.methods:
                for method in manifest.api.methods:
                    data['api_endpoints'].append({
                        'feature': manifest.name,
                        'method': method.verb,
                        'path': f"/api/{key}{method.path}",
                        'name': method.name
                    })
            
            # Environment variables
            if manifest.config and manifest.config.env:
                for env_key, field in manifest.config.env.items():
                    data['env_vars'].append({
                        'name': env_key,
                        'feature': manifest.name,
                        'description': field.description or '',
                        'required': field.required if hasattr(field, 'required') else False,
                        'default': str(field.default) if field.default else ''
                    })
            
            # Detect capabilities
            if manifest.classification.capability == 'agent':
                data['capabilities']['has_agent'] = True
            elif manifest.classification.capability == 'tool':
                data['capabilities']['has_tools'] = True
            
            key_lower = key.lower()
            if 'llm' in key_lower or 'gemini' in key_lower or 'openai' in key_lower:
                data['capabilities']['has_llm'] = True
            if 'vector' in key_lower or 'chroma' in key_lower:
                data['capabilities']['has_vector_db'] = True
            if 'memory' in key_lower or 'session' in key_lower:
                data['capabilities']['has_memory'] = True
            
            data['features'].append(feature_info)
        
        return data
    
    def _generate_with_llm(
        self, 
        features_data: Dict, 
        execution_mode: str, 
        frontend_mode: str,
        has_docker: bool
    ) -> str:
        """Generate README using LLM"""
        print(" [DocsGen] Calling LLM for README generation...")
        
        # Build prompt
        prompt = self._build_llm_prompt(features_data, execution_mode, frontend_mode, has_docker)
        
        # Call LLM (using existing llm-universal feature)
        try:
            from app.services.library_service import library_service
            
            # Get LLM adapter
            llm_adapter = library_service.import_runtime_adapter('llm-universal')
            
            # Call LLM
            result = llm_adapter.run(
                inputs={'prompt': prompt},
                context={}
            )
            
            if result.get('success'):
                readme = result.get('response', '')
                print(" [DocsGen] LLM generation successful")
                return readme
            else:
                raise Exception(result.get('error', 'LLM call failed'))
        
        except Exception as e:
            print(f" [DocsGen] LLM call failed: {e}")
            raise
    
    def _build_llm_prompt(
        self,
        features_data: Dict,
        execution_mode: str,
        frontend_mode: str,
        has_docker: bool
    ) -> str:
        """Build LLM prompt for README generation"""
        
        # Format features list
        features_list = []
        for feat in features_data['features']:
            features_list.append(f"- {feat['name']} ({feat['category']}): {feat['description']}")
        
        # Format env vars
        env_list = []
        for env in features_data['env_vars']:
            req = "Required" if env['required'] else "Optional"
            env_list.append(f"- {env['name']} ({req}): {env['description']} [Used by: {env['feature']}]")
        
        # Format API endpoints
        api_list = []
        for api in features_data['api_endpoints']:
            api_list.append(f"- {api['method']} {api['path']} - {api['feature']}")
        
        prompt = f"""You are a technical documentation expert. Generate a professional, comprehensive README.md file for a software project.

PROJECT INFORMATION:
- Project Name: {features_data['project_name']}
- Type: {execution_mode} (agent/conversational/pipeline/api)
- Interface: {frontend_mode} (generated_ui/external_extension/headless)
- Has Docker: {has_docker}

FEATURES INCLUDED:
{chr(10).join(features_list)}

CAPABILITIES:
- AI Agent: {features_data['capabilities']['has_agent']}
- Tool Calling: {features_data['capabilities']['has_tools']}
- LLM Integration: {features_data['capabilities']['has_llm']}
- Vector Database: {features_data['capabilities']['has_vector_db']}
- Memory: {features_data['capabilities']['has_memory']}

ENVIRONMENT VARIABLES:
{chr(10).join(env_list) if env_list else "None"}

API ENDPOINTS:
{chr(10).join(api_list) if api_list else "None (no API endpoints)"}

REQUIREMENTS:
Generate a README.md that includes:

1. **Project Title and Description**: Clear, engaging overview of what this project does
2. **Features**: Highlight key capabilities based on the features list above
3. **Prerequisites**: List required software (Python 3.11+, Node.js if needed, API keys)
4. **Installation**:
   - Docker setup (if has_docker is True)
   - Manual setup for backend
   - Frontend setup (if frontend_mode is 'generated_ui')
5. **Configuration**: Explain environment variables that need to be set
6. **Usage**: How to run and use the application
7. **API Documentation**: Document the API endpoints (if any)
8. **Architecture**: Brief overview of the system architecture
9. **Troubleshooting**: Common issues and solutions
10. **License**: MIT License

FORMATTING REQUIREMENTS:
- Use proper Markdown formatting
- Include code blocks with bash/python/javascript syntax highlighting where appropriate
- Use emojis sparingly for section headers (📋 ⚙️ 🚀 etc.)
- Be concise but comprehensive
- Write in a professional, developer-friendly tone
- Focus on practical information that helps users get started quickly

Generate ONLY the README.md content. Do not include any preamble or explanation - start directly with the markdown content."""

        return prompt
    
    def _generate_template(
        self,
        features_data: Dict,
        execution_mode: str,
        frontend_mode: str,
        has_docker: bool
    ) -> str:
        """Fallback template generation"""
        
        features_text = '\n'.join([f"- **{f['name']}**: {f['description']}" for f in features_data['features']])
        
        return f"""# {features_data['project_name']}

## Overview

This is a {execution_mode} application with {frontend_mode} interface.

## Features

{features_text}

## Setup

### Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.template .env
python app.py
```

{'### Frontend\n```bash\ncd frontend\nnpm install\nnpm run dev\n```' if frontend_mode == 'generated_ui' else ''}

## Environment Variables

See `.env.template` for configuration options.

## Usage

Start the backend and access at http://localhost:8000

Generated by AI Builder Platform.
"""
from typing import Dict, List
from app.services.library_service import library_service
from ..errors.packager_errors import CodeGenerationError


class DockerGenerator:
    """Generates Docker configuration files"""
    
    def __init__(self, project_name: str):
        self.project_name = project_name
    
    def generate(self, feature_keys: List[str]) -> Dict[str, str]:
        """
        Generate Docker files
        Returns dict: {filepath: content}
        """
        print("🐳 [DockerGen] Generating Docker configuration...")
        
        try:
            files = {}
            
            # Detect required services
            services = self._detect_services(feature_keys)
            
            # Generate Dockerfile for backend
            files['backend/Dockerfile'] = self._generate_backend_dockerfile()
            
            # Generate Dockerfile for frontend
            files['frontend/Dockerfile'] = self._generate_frontend_dockerfile()
            
            # Generate docker-compose.yml
            files['docker-compose.yml'] = self._generate_compose(services)
            
            # Generate .dockerignore
            files['backend/.dockerignore'] = self._generate_dockerignore()
            files['frontend/.dockerignore'] = self._generate_dockerignore()
            
            print(f" [DockerGen] Generated {len(files)} Docker files")
            return files
        
        except Exception as e:
            print(f" [DockerGen] Error: {e}")
            raise CodeGenerationError(f"Docker generation failed: {e}")
    
    def _detect_services(self, feature_keys: List[str]) -> Dict[str, bool]:
        """Detect which services are needed"""
        services = {
            'redis': False,
            'postgres': False,
            'chroma': False
        }
        
        for key in feature_keys:
            manifest = library_service.get_feature(key)
            if not manifest:
                continue
            
            # Check feature dependencies
            feature_name = manifest.name.lower()
            
            if 'redis' in feature_name or 'session' in feature_name:
                services['redis'] = True
            
            if 'postgres' in feature_name or 'database' in feature_name:
                services['postgres'] = True
            
            if 'chroma' in feature_name or 'vector' in feature_name:
                services['chroma'] = True
        
        return services
    
    def _generate_backend_dockerfile(self) -> str:
        """Generate backend Dockerfile"""
        return """FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["python", "app.py"]
"""
    
    def _generate_frontend_dockerfile(self) -> str:
        """Generate frontend Dockerfile"""
        return """FROM node:18-alpine as build

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json* ./
RUN npm install

# Copy source
COPY . .

# Build
RUN npm run build

# Production image
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
"""
    
    def _generate_compose(self, services: Dict[str, bool]) -> str:
        """Generate docker-compose.yml"""
        
        service_definitions = []
        
        # Backend service
        service_definitions.append("""
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - PORT=8000
    env_file:
      - ./backend/.env
    depends_on:""")
        
        # Add dependencies
        deps = []
        if services['redis']:
            deps.append("      - redis")
        if services['postgres']:
            deps.append("      - postgres")
        if services['chroma']:
            deps.append("      - chroma")
        
        if deps:
            service_definitions.append('\n'.join(deps))
        else:
            service_definitions.append("      []")
        
        # Frontend service
        service_definitions.append("""
  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend""")
        
        # Redis service
        if services['redis']:
            service_definitions.append("""
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data""")
        
        # Postgres service
        if services['postgres']:
            service_definitions.append("""
  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=app
      - POSTGRES_USER=app
      - POSTGRES_PASSWORD=changeme
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data""")
        
        # Chroma service
        if services['chroma']:
            service_definitions.append("""
  chroma:
    image: ghcr.io/chroma-core/chroma:latest
    ports:
      - "8001:8000"
    volumes:
      - chroma_data:/chroma/chroma""")
        
        # Volumes section
        volumes = []
        if services['redis']:
            volumes.append("  redis_data:")
        if services['postgres']:
            volumes.append("  postgres_data:")
        if services['chroma']:
            volumes.append("  chroma_data:")
        
        volumes_section = ""
        if volumes:
            volumes_section = "\nvolumes:\n" + "\n".join(volumes)
        
        return f"""version: '3.8'

services:
{''.join(service_definitions)}
{volumes_section}
"""
    
    def _generate_dockerignore(self) -> str:
        """Generate .dockerignore"""
        return """node_modules
__pycache__
*.pyc
.env
.git
.vscode
*.log
dist
build
"""
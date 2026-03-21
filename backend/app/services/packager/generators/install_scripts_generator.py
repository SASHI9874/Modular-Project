from typing import Dict


class InstallScriptsGenerator:
    """Generates installation scripts for downloaded packages"""
    
    def __init__(self, project_name: str):
        self.project_name = project_name
    
    def generate(self, has_frontend: bool, has_extension: bool, extension_name: str = None) -> Dict[str, str]:
        """
        Generate install scripts
        
        Returns:
            Dict of {filepath: content}
        """
        print(" [InstallScripts] Generating install scripts...")
        
        files = {}
        
        # Generate bash script (Linux/Mac)
        files['install.sh'] = self._generate_bash_script(has_frontend, has_extension, extension_name)
        
        # Generate batch script (Windows)
        files['install.bat'] = self._generate_batch_script(has_frontend, has_extension, extension_name)
        
        # Generate README for installation
        files['INSTALL.md'] = self._generate_install_readme(has_frontend, has_extension, extension_name)
        
        print(f" [InstallScripts] Generated {len(files)} install files")
        return files
    
    def _generate_bash_script(self, has_frontend: bool, has_extension: bool, extension_name: str) -> str:
        """Generate bash install script"""
        
        script = """#!/bin/bash

set -e  # Exit on error

echo "=========================================="
echo "Installing {project_name}"
echo "=========================================="

# Check prerequisites
echo ""
echo "Checking prerequisites..."

if ! command -v python3 &> /dev/null; then
    echo " Python 3 is required but not installed"
    exit 1
fi
echo " Python 3 found"

if ! command -v pip &> /dev/null; then
    echo " pip is required but not installed"
    exit 1
fi
echo " pip found"
""".format(project_name=self.project_name)

        if has_frontend:
            script += """
if ! command -v node &> /dev/null; then
    echo " Node.js is required but not installed"
    exit 1
fi
echo " Node.js found"

if ! command -v npm &> /dev/null; then
    echo " npm is required but not installed"
    exit 1
fi
echo " npm found"
"""

        script += """
# Install backend
echo ""
echo "Installing backend..."
cd backend
pip install -r requirements.txt
cp .env.template .env
echo " Backend installed"
cd ..
"""

        if has_frontend:
            script += """
# Install frontend
echo ""
echo "Installing frontend..."
cd frontend
npm install
echo " Frontend installed"
cd ..
"""

        if has_extension and extension_name:
            script += f"""
# Install VS Code extension
echo ""
echo "Installing VS Code extension..."
if command -v code &> /dev/null; then
    code --install-extension {extension_name}
    echo " Extension installed"
else
    echo "  VS Code not found - skipping extension installation"
    echo "   Install manually: code --install-extension {extension_name}"
fi
"""

        script += """
echo ""
echo "=========================================="
echo "Installation complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit backend/.env with your API keys"
"""

        if has_frontend:
            script += """echo "2. Start backend: cd backend && python app.py"
echo "3. Start frontend: cd frontend && npm run dev"
"""
        else:
            script += """echo "2. Start backend: cd backend && python app.py"
"""

        return script
    
    def _generate_batch_script(self, has_frontend: bool, has_extension: bool, extension_name: str) -> str:
        """Generate Windows batch script"""
        
        script = """@echo off
setlocal enabledelayedexpansion

echo ==========================================
echo Installing {project_name}
echo ==========================================

REM Check prerequisites
echo.
echo Checking prerequisites...

where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo X Python 3 is required but not installed
    exit /b 1
)
echo √ Python 3 found

where pip >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo X pip is required but not installed
    exit /b 1
)
echo √ pip found
""".format(project_name=self.project_name)

        if has_frontend:
            script += """
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo X Node.js is required but not installed
    exit /b 1
)
echo √ Node.js found

where npm >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo X npm is required but not installed
    exit /b 1
)
echo √ npm found
"""

        script += """
REM Install backend
echo.
echo Installing backend...
cd backend
pip install -r requirements.txt
copy .env.template .env
echo √ Backend installed
cd ..
"""

        if has_frontend:
            script += """
REM Install frontend
echo.
echo Installing frontend...
cd frontend
call npm install
echo √ Frontend installed
cd ..
"""

        if has_extension and extension_name:
            script += f"""
REM Install VS Code extension
echo.
echo Installing VS Code extension...
where code >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    code --install-extension {extension_name}
    echo √ Extension installed
) else (
    echo ! VS Code not found - skipping extension installation
    echo   Install manually: code --install-extension {extension_name}
)
"""

        script += """
echo.
echo ==========================================
echo Installation complete!
echo ==========================================
echo.
echo Next steps:
echo 1. Edit backend\\.env with your API keys
"""

        if has_frontend:
            script += """echo 2. Start backend: cd backend ^&^& python app.py
echo 3. Start frontend: cd frontend ^&^& npm run dev
"""
        else:
            script += """echo 2. Start backend: cd backend ^&^& python app.py
"""

        script += """
pause
"""

        return script
    
    def _generate_install_readme(self, has_frontend: bool, has_extension: bool, extension_name: str) -> str:
        """Generate installation README"""
        
        readme = f"""# Installation Guide - {self.project_name}

## Automated Installation

### Linux/Mac
```bash
chmod +x install.sh
./install.sh
```

### Windows
```bash
install.bat
```

## Manual Installation

### Prerequisites
- Python 3.11+
- pip
"""

        if has_frontend:
            readme += """- Node.js 18+
- npm
"""

        if has_extension:
            readme += """- VS Code (for extension)
"""

        readme += """
### Step 1: Backend Setup
```bash
cd backend
pip install -r requirements.txt
cp .env.template .env
```

Edit `.env` with your configuration (API keys, etc.)
```bash
python app.py
```

Backend runs at: http://localhost:8000
"""

        if has_frontend:
            readme += """
### Step 2: Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Frontend runs at: http://localhost:5173
"""

        if has_extension and extension_name:
            readme += f"""
### Step 3: VS Code Extension
```bash
code --install-extension {extension_name}
```

Restart VS Code after installation.
"""

        readme += """
## Troubleshooting

### Backend won't start
- Verify Python version: `python --version` (should be 3.11+)
- Check dependencies: `pip list`
- Verify `.env` file exists with required keys

"""

        if has_frontend:
            readme += """### Frontend won't start
- Verify Node version: `node --version` (should be 18+)
- Clear cache: `rm -rf node_modules && npm install`
- Check backend is running

"""

        readme += """### Need help?
Check the main README.md for more information.
"""

        return readme
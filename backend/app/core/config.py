# import os

# # Define the root of project dynamically
# BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# REPO_PATH = os.path.join(BASE_DIR, "modules_repo")

import os
from pathlib import Path

class Settings:
    # 1. Get the path to this file (backend/core/config.py)
    # 2. Go up 2 levels: core -> backend
    BASE_DIR = Path(__file__).resolve().parent.parent.parent

    # Define paths relative to the backend folder
    REPO_PATH = BASE_DIR / "modules_repo"
    BUILD_DIR = BASE_DIR / "build_temp"
    OUTPUT_DIR = BASE_DIR / "output_wheels"
    
    # Default Configs
    PACKAGE_NAME = "my_custom_ai_sdk"

    # Optional: Create directories if they don't exist when config is loaded
    def ensure_dirs(self):
        self.BUILD_DIR.mkdir(parents=True, exist_ok=True)
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

settings = Settings()
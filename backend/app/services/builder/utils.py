import os
import shutil
import stat
import json 
from typing import List, Set
from app.core.config import settings

def remove_readonly(func, path, _):
    """Windows helper to force delete read-only files."""
    os.chmod(path, stat.S_IWRITE)
    func(path)

def clean_build_dirs():
    """Safely cleans build and output directories."""
    for directory in [settings.BUILD_DIR, settings.OUTPUT_DIR]:
        if directory.exists():
            # Use the error handler for Windows permissions
            shutil.rmtree(directory, onerror=remove_readonly)
    
    # Recreate output dir
    settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def merge_requirements(selected_features: List[str]) -> List[str]:
    """Merges requirements.txt from all selected features."""
    merged_reqs: Set[str] = set()
    
    for feature in selected_features:
        req_path = settings.REPO_PATH / feature / "requirements.txt"
        if req_path.exists():
            with open(req_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        merged_reqs.add(line)
    
    return list(merged_reqs)

def get_feature_metadata(feature_dir_name: str) -> dict:
    """
    Reads the meta.json for a specific feature.
    """
    meta_path = settings.REPO_PATH / feature_dir_name / "meta.json"
    
    if meta_path.exists():
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Ensure 'id' exists, default to folder name if missing
                if "id" not in data: 
                    data["id"] = feature_dir_name
                return data
        except Exception as e:
            print(f"❌ Error reading meta.json for {feature_dir_name}: {e}")

    # Fallback if meta.json is missing or broken
    return {
        "id": feature_dir_name,
        "class_name": "UnknownProcessor", 
        "name": feature_dir_name
    }
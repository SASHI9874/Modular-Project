import os
import json
from app.core.config import settings

def scan_available_features():
    """
    Scans:
    1. settings.REPO_PATH -> for Core Modules
    2. settings.REPO_PATH/user_defined -> for Custom Modules
    """
    features = []
    repo_path = settings.REPO_PATH
    
    if not os.path.exists(repo_path):
        return []

    # --- 1. SCAN CORE MODULES (Root Level) ---
    for item in os.listdir(repo_path):
        item_path = os.path.join(repo_path, item)
        
        # Skip the 'user_defined' folder (we handle it in step 2)
        if item == "user_defined":
            continue
            
        meta_path = os.path.join(item_path, "meta.json")
        
        # If it's a directory and has meta.json, it's a CORE module
        if os.path.isdir(item_path) and os.path.exists(meta_path):
            try:
                with open(meta_path, "r") as f:
                    meta = json.load(f)
                    features.append(meta)
            except Exception as e:
                print(f"Error reading core module {item}: {e}")

    # --- 2. SCAN CUSTOM MODULES (Inside user_defined folder) ---
    custom_repo_path = os.path.join(repo_path, "user_defined")
    
    if os.path.exists(custom_repo_path):
        for item in os.listdir(custom_repo_path):
            item_path = os.path.join(custom_repo_path, item)
            meta_path = os.path.join(item_path, "meta.json")
            
            # If it's a directory and has meta.json, it's a CUSTOM module
            if os.path.isdir(item_path) and os.path.exists(meta_path):
                try:
                    with open(meta_path, "r") as f:
                        meta = json.load(f)
                        features.append(meta) # Simply append what is in the file
                except Exception as e:
                    print(f"Error reading custom module {item}: {e}")
                
    return features
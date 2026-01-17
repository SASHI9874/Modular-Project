import os
import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MODULES_REPO = BASE_DIR / "modules_repo"
GLOBAL_REQS = BASE_DIR / "requirements.txt"

def install_requirements(file_path: Path):
    """Runs pip install for a specific file."""
    if not file_path.exists():
        print(f"⚠️  Skipping missing file: {file_path}")
        return

    print(f"📦 Installing from: {file_path.name} ({file_path.parent.name})...")
    try:
        # We use sys.executable to ensure we use the SAME python interpreter (the venv)
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", str(file_path)]
        )
        print("✅ Success!\n")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {file_path}. Error: {e}\n")

def main():
    print("🚀 Starting Bulk Dependency Installation...\n")

    # 1. Install Global Requirements
    if GLOBAL_REQS.exists():
        print("🌍 Installing Global Requirements...")
        install_requirements(GLOBAL_REQS)
    else:
        print("⚠️  No global requirements.txt found.")

    # 2. Scan Modules Repo for Feature Requirements
    if MODULES_REPO.exists():
        print(f"🔍 Scanning features in: {MODULES_REPO}...\n")
        
        # Iterate over all folders in modules_repo
        for feature_dir in MODULES_REPO.iterdir():
            if feature_dir.is_dir():
                req_path = feature_dir / "requirements.txt"
                if req_path.exists():
                    install_requirements(req_path)
    else:
        print(f"⚠️  Modules repo not found at {MODULES_REPO}")

    print("🎉 All dependencies processed.")

if __name__ == "__main__":
    main()
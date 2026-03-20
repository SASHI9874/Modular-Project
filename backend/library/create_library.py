import sys
from pathlib import Path

def create_library_structure(library_name: str):
    # Get the directory where this script is currently saved
    script_dir = Path(__file__).parent
    
    # Set the base directory path to be right next to the script
    base_path = script_dir / library_name

    # Define the directory tree
    DIRECTORIES = [
        "core",
        "runtime",
        "generator/backend",
        "generator/frontend"
    ]

    # Define the files to create
    FILES = [
        "feature.spec.json",
        "core/__init__.py",
        "core/service.py",        
        "runtime/adapter.py",
        "generator/backend/routes.py",
        "generator/frontend/component.tsx",
        "requirements.txt",
        "README.md"
    ]

    print(f"🚀 Generating structure for library: {library_name}...\n")

    try:
        # 1. Create all directories (parents=True ensures nested folders are made)
        for directory in DIRECTORIES:
            dir_path = base_path / directory
            dir_path.mkdir(parents=True, exist_ok=True)

        # 2. Create all empty files
        for file in FILES:
            file_path = base_path / file
            # Ensure the parent directory exists before creating the file
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.touch(exist_ok=True)
            print(f"📄 Created: {file}")

        print(f"\n✅ Success! '{library_name}' is ready at: {base_path}")

    except Exception as e:
        print(f"\n❌ An error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python create_library.py <library_name>")
        print("Example: python create_library.py code-intelligence")
        sys.exit(1)

    lib_name = sys.argv[1]
    create_library_structure(lib_name)
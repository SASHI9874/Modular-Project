import os
import json
import importlib.util
from typing import Dict, List, Optional

from pathlib import Path as FilePath
from app.schemas.feature_spec import FeatureManifest

class LibraryService:
    def __init__(self, library_path: str = "library"):
        # Robust path resolution: Handles running from root vs inside app/
        base_dir = FilePath(__file__).resolve().parent.parent.parent
        self.library_path = base_dir / "library"
        print("Resolved library path:", self.library_path)            
        self.features: Dict[str, FeatureManifest] = {}
        # We auto-scan on initialization
        self.scan()

    def scan(self):
        """Walks the library directory and loads feature.spec.json files."""
        print(f" Scanning Library at: {self.library_path}")
        self.features = {} # Reset
        print("library path ",self.library_path)
        if not os.path.exists(self.library_path):
            print(f"❌ Library path not found: {self.library_path}")
            return

        for folder_name in os.listdir(self.library_path):
            folder_path = os.path.join(self.library_path, folder_name)
            spec_path = os.path.join(folder_path, "feature.spec.json")
            
            # We only care about directories that have a spec file
            if os.path.isdir(folder_path) and os.path.exists(spec_path):
                try:
                    with open(spec_path, "r") as f:
                        data = json.load(f)
                    
                    # VALIDATION: Pydantic ensures the JSON matches our strict Schema
                    manifest = FeatureManifest(**data)
                    manifest.base_path = folder_path
                    
                    self.features[manifest.key] = manifest
                    print(f"   ✅ Loaded: {manifest.name} ({manifest.key})")
                    
                except Exception as e:
                    print(f"   ❌ Error loading {folder_name}: {e}")

    def get_feature(self, key: str) -> Optional[FeatureManifest]:
        return self.features.get(key)

    def get_all_features(self) -> List[FeatureManifest]:
        return list(self.features.values())

    def import_runtime_adapter(self, key: str):
        """
        Dynamically imports library.<feature>.runtime.adapter
        """

        feature = self.get_feature(key)
        if not feature:
            raise ValueError(f"Feature '{key}' not found")

        from pathlib import Path
        import sys, importlib.util, traceback

        # --- Ensure project root is importable (only once) ---
        project_root = Path(__file__).resolve().parents[2]
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))

        # --- Build real file path ---
        adapter_path = (Path(feature.base_path) / feature.paths.runtime).resolve()

        if not adapter_path.is_file():
            raise FileNotFoundError(f"Adapter file not found: {adapter_path}")

        # --- Real package-style module name ---
        module_name = f"library.{key}.runtime.adapter"

        # --- Avoid reloading same module ---
        if module_name in sys.modules:
            return sys.modules[module_name]

        spec = importlib.util.spec_from_file_location(module_name, str(adapter_path))
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not create import spec for {adapter_path}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module  # required for relative imports to work

        try:
            spec.loader.exec_module(module)
        except Exception:
            print(f"🔥 Error loading runtime adapter: {module_name}")
            traceback.print_exc()
            del sys.modules[module_name]  # cleanup broken module
            raise

        print(f"✅ Loaded runtime adapter: {module_name}")
        return module


# Singleton Instance
library_service = LibraryService()
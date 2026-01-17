import os
import shutil
from pathlib import Path
import uuid

class StorageManager:
    def __init__(self):
        self.BASE_DIR = Path(__file__).resolve().parent.parent.parent / "storage"
        
        # Sub-directories
        self.UPLOAD_DIR = self.BASE_DIR / "uploads"
        self.VECTOR_DIR = self.BASE_DIR / "vectors"
        
        # Ensure roots exist
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        self.VECTOR_DIR.mkdir(parents=True, exist_ok=True)

    def _get_unique_path(self, directory: Path, filename: str) -> Path:
        """
        Recursive check: If 'report.pdf' exists, return 'report_1.pdf'.
        If 'report_1.pdf' exists, return 'report_2.pdf', etc.
        """
        file_path = directory / filename
        
        if not file_path.exists():
            return file_path
        
        # Split 'report' and '.pdf'
        stem = file_path.stem
        suffix = file_path.suffix
        counter = 1
        
        while True:
            new_filename = f"{stem}_{counter}{suffix}"
            new_path = directory / new_filename
            if not new_path.exists():
                return new_path
            counter += 1

    def save_upload(self, source_path: str, session_id: str, original_filename: str = None) -> str:
        """
        Moves a file from temp location to storage/uploads/{session_id}/
        Uses UUID prefix to ensure unique filenames and prevent race conditions.
        """
        source = Path(source_path)
        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        filename = original_filename if original_filename else source.name

        # 1. Create Session Folder inside Uploads
        session_dir = self.UPLOAD_DIR / session_id
        session_dir.mkdir(parents=True, exist_ok=True)

        # 2. Generate Unique Destination Path with UUID prefix
        safe_filename = f"{uuid.uuid4().hex[:8]}_{filename}"
        destination = session_dir / safe_filename

        # 3. Copy the file
        print(f"Storage: Saving {filename} -> {destination}")
        shutil.copy2(source, destination)

        return str(destination.absolute())

    def get_vector_path(self, session_id: str, filename: str) -> str:
        """
        Returns a path for vector DBs: storage/vectors/{session_id}/{filename}
        """
        session_vec_dir = self.VECTOR_DIR / session_id
        session_vec_dir.mkdir(parents=True, exist_ok=True)
        return str(session_vec_dir / filename)

from pathlib import Path
from app.services.storage_service import StorageManager

class FileUploader:
    def __init__(self):
        self.storage = StorageManager()

    def run(self, file_path: str):
        """
        Moves the temporary uploaded file to permanent storage.
        """
        if not file_path:
            raise ValueError("No file provided.")

        source = Path(file_path)
        
        # 1. Extract Session ID from the temp path
        # Structure is: backend/temp_uploads/{session_id}/{filename}
        # So parent.name gives us the session_id
        session_id = source.parent.name
        saved_path = self.storage.save_upload(source, session_id)
        
        return saved_path
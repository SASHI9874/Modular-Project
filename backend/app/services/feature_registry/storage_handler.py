from minio import Minio
from app.core.config import settings
import io

class MinioHandler:
    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT.replace("http://", "").replace("https://", ""),
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self.bucket_name = settings.MINIO_BUCKET_NAME
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        if not self.client.bucket_exists(self.bucket_name):
            self.client.make_bucket(self.bucket_name)

    def upload_code(self, filename: str, data: bytes) -> str:
        """
        Uploads bytes to MinIO and returns the reference path.
        Example Path: s3://feature-store/my-feature/v1.0.0/code.py
        """
        file_stream = io.BytesIO(data)
        file_size = len(data)
        
        self.client.put_object(
            self.bucket_name,
            filename,
            file_stream,
            file_size,
            content_type="application/x-python-code"
        )
        return f"s3://{self.bucket_name}/{filename}"

storage = MinioHandler()
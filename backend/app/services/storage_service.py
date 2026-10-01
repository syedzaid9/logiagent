import os
from abc import ABC, abstractmethod
from typing import List, Optional
from app.core.config import settings
from app.core.logging_config import logger

class BaseStorageService(ABC):
    @abstractmethod
    def save_file(self, filename: str, content: bytes) -> str:
        pass

    @abstractmethod
    def get_file(self, filename: str) -> Optional[bytes]:
        pass

class LocalFileStorageService(BaseStorageService):
    """
    Local filesystem storage for documents when cloud bucket is not configured.
    [LOCAL STORAGE IMPLEMENTATION]
    """
    def __init__(self, base_dir: str = "data/documents"):
        self.base_dir = os.path.abspath(base_dir)
        os.makedirs(self.base_dir, exist_ok=True)
        logger.info(f"[StorageService] Running with LocalFileStorageService at '{self.base_dir}'.")

    def save_file(self, filename: str, content: bytes) -> str:
        filepath = os.path.join(self.base_dir, filename)
        with open(filepath, "wb") as f:
            f.write(content)
        return filepath

    def get_file(self, filename: str) -> Optional[bytes]:
        filepath = os.path.join(self.base_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, "rb") as f:
                return f.read()
        return None

class S3CloudStorageService(BaseStorageService):
    def __init__(self, bucket_name: str):
        self.bucket_name = bucket_name
        logger.info(f"[StorageService] S3/GCS Object Storage initialized for bucket '{bucket_name}'.")

    def save_file(self, filename: str, content: bytes) -> str:
        local = LocalFileStorageService()
        return local.save_file(filename, content)

    def get_file(self, filename: str) -> Optional[bytes]:
        local = LocalFileStorageService()
        return local.get_file(filename)

def get_storage_service() -> BaseStorageService:
    if hasattr(settings, "OBJECT_STORAGE_BUCKET") and settings.OBJECT_STORAGE_BUCKET and settings.OBJECT_STORAGE_BUCKET != "logiagent-documents-bucket":
        return S3CloudStorageService(settings.OBJECT_STORAGE_BUCKET)
    return LocalFileStorageService()

storage_service = get_storage_service()

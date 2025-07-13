# utilities_module/blob_utils.py
import uuid
from config import blob_service_client

def upload_file_to_blob(container_name: str, file_bytes: bytes, file_extension: str) -> str:
    """Uploads file bytes to Azure Blob Storage and returns the blob's URL."""
    try:
        blob_name = f"{str(uuid.uuid4())}.{file_extension}"
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
        blob_client.upload_blob(file_bytes, overwrite=True)
        return blob_client.url
    except Exception as e:
        print(f"Error uploading to blob: {e}")
        return None
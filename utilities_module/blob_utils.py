# utilities_module/blob_utils.py

from azure.storage.blob import BlobServiceClient
import uuid

def upload_to_blob_storage(blob_service_client: BlobServiceClient, container_name: str, file_bytes: bytes, file_extension: str) -> str:
    """
    Uploads a file to Azure Blob Storage and returns the blob's URL.

    Args:
        blob_service_client: The initialized BlobServiceClient.
        container_name: The name of the blob container (e.g., 'images' or 'audio').
        file_bytes: The file content in bytes.
        file_extension: The file extension (e.g., 'jpg', 'wav').

    Returns:
        The URL of the uploaded blob.
    """
    # Create a unique name for the blob to avoid overwriting files
    blob_name = f"{str(uuid.uuid4())}.{file_extension}"
    
    # Get a client to interact with the specific blob
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
    
    # Upload the data
    blob_client.upload_blob(file_bytes, overwrite=True)
    print(f"Uploaded {blob_name} to container '{container_name}'.")
    
    # Return the full URL of the uploaded blob
    return blob_client.url
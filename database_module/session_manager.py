# database_module/session_manager.py
# Manages the lifecycle of chat sessions.


import uuid
import json
from datetime import datetime, timezone



def create_new_chat_session(user_id: str, session_title: str) -> str:
    """Creates a session in Cosmos DB and an empty log file in Blob. Returns session_id."""
    # <<< CHANGE: Imports are moved inside the function >>>
    from config import chat_history_container_client, blob_service_client, CHAT_LOG_BLOB_CONTAINER_NAME

    session_id = str(uuid.uuid4())
    blob_name = f"{session_id}.json"
    
    blob_client = blob_service_client.get_blob_client(container=CHAT_LOG_BLOB_CONTAINER_NAME, blob=blob_name)
    blob_client.upload_blob(json.dumps([]), overwrite=True)

    session_document = {
        "id": session_id,
        "partitionKey": user_id,
        "user_id": user_id,
        "session_title": session_title,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "chat_log_blob_url": blob_client.url
    }

    chat_history_container_client.create_item(body=session_document)
    return session_id

def add_message_to_log(session_id: str, user_id: str, message_dict: dict):
    """Appends a message to a session's chat log in Blob Storage."""
    
    from config import chat_history_container_client, blob_service_client, CHAT_LOG_BLOB_CONTAINER_NAME

    session_doc = chat_history_container_client.read_item(item=session_id, partition_key=user_id)
    
    blob_client = blob_service_client.get_blob_client(
        container=CHAT_LOG_BLOB_CONTAINER_NAME, 
        blob=session_doc['chat_log_blob_url'].split('/')[-1]
    )
    
    downloader = blob_client.download_blob()
    chat_log_list = json.loads(downloader.readall())
    
    chat_log_list.append(message_dict)
    
    blob_client.upload_blob(json.dumps(chat_log_list), overwrite=True)
    
    session_doc['last_updated'] = datetime.now(timezone.utc).isoformat()
    chat_history_container_client.replace_item(item=session_id, body=session_doc)
    print(f"Appended message to log for session {session_id} and updated timestamp.")
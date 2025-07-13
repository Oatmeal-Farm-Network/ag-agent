# utilities_module/memory_processor.py
# Processes text and creates searchable vector memories in Cosmos DB.

import uuid
from datetime import datetime, timezone

from .embedding_utils import get_embedding
from memory_module.langchain_setup import vector_store, get_session_history  # Importing LangChain components


def add_text_memory_cosmos(text_content: str, user_id: str, session_id: str) -> bool:
    """
    Takes text, generates an embedding, and stores it as a searchable memory in Cosmos DB.
    """
    from config import container_client
    
    if not text_content:
        print("Skipping memory creation: No text content provided.")
        return False
    
    embedding = get_embedding(text_content)
    if embedding is None:
        print("Failed to create embedding. Memory not stored.")
        return False
        
    memory_document = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "session_id": session_id,
        "text": text_content,
        "embedding": embedding.tolist(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    try:
        container_client.create_item(body=memory_document)
        print(f"Successfully created text memory. ID: {memory_document['id']}")
        return True
    except Exception as e:
        print(f"Failed to save text memory to Cosmos DB: {e}")
        return False


def add_text_memory_langchain(text_content: str, user_id: str, session_id: str) -> bool:
    """Adds text to the user's long-term memory using LangChain vector store."""
    try:
        # Add to vector store for long-term memory
        vector_store.add_texts([text_content], metadatas=[{"user_id": user_id, "session_id": session_id}])
        print(f"Successfully added memory to vector store for user {user_id}")
        return True
    except Exception as e:
        print(f"Failed to add memory using LangChain vector store: {e}")
        return False


def add_chat_memory(text_content: str, user_id: str, session_id: str, message_type: str = "human") -> bool:
    """Adds text to the user's short-term chat history using LangChain."""
    try:
        # Get chat history for the session
        chat_history = get_session_history(session_id, user_id)
        
        # Add message to chat history
        if message_type.lower() == "human":
            chat_history.add_user_message(text_content)
        else:
            chat_history.add_ai_message(text_content)
            
        print(f"Successfully added chat message for user {user_id}")
        return True
    except Exception as e:
        print(f"Failed to add chat message using LangChain: {e}")
        return False


def add_text_memory(text_content: str, user_id: str, session_id: str, use_langchain: bool = True) -> bool:
    """
    Unified function to add text memory. Uses LangChain by default, falls back to Cosmos DB if needed.
    """
    if use_langchain:
        return add_text_memory_langchain(text_content, user_id, session_id)
    else:
        return add_text_memory_cosmos(text_content, user_id, session_id)
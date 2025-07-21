# cosmos_retriever.py
# This file is dedicated to functions that interact with Azure Cosmos DB, Blob Storage
# primarily for performing semantic searches and storing multimodal data.

# --- Imports ---
from typing import List, Dict, Optional
import numpy as np
from azure.cosmos import exceptions as CosmosExceptions
from datetime import datetime
import uuid

#from config import (
#    container_client,
#    livestock_container_client,
#    chat_history_container_client,
    #image_embeddings_container_client,
    #audio_embeddings_container_client,
    #blob_service_client,
    #IMAGE_BLOB_CONTAINER_NAME,
    #AUDIO_BLOB_CONTAINER_NAME
#)
from utilities_module.embedding_utils import get_embedding
from utilities_module.blob_utils import upload_to_blob_storage
from utilities_module.audio_utils import transcribe_audio_to_text


# --- Data Retrieval Functions ---

def retrieve_semantic_chunks_tool(query_text: str, user_id, k: int = 3) -> str:
    """Retrieves relevant text chunks from the general knowledge container."""
    if container_client is None:
        return "Error: General knowledge container client not initialized."
    query_embedding_np = get_embedding(query_text)
    if query_embedding_np is None:
        return "Failed to get query embedding. Cannot retrieve chunks."
    
    query_embedding_list = query_embedding_np.tolist()
    query_str = (
        f"SELECT TOP {k} c.id, c.text, VectorDistance(c.embedding, @queryEmbedding) AS score "
        f"FROM c ORDER BY VectorDistance(c.embedding, @queryEmbedding)"
    )
    params = [{"name": "@queryEmbedding", "value": query_embedding_list}]

    try:
        items = container_client.query_items(query=query_str, parameters=params, enable_cross_partition_query=True)
        chunks = [{"id": item.get("id"), "text": item.get("text", ""), "score": item.get("score")} for item in items]
    except Exception as e:
        return f"An unexpected error occurred while querying Cosmos DB: {e}"

    if not chunks:
        return "No relevant information found."
        
    formatted_chunks = "\n\n---\n\n".join(
        [f"Snippet {i+1} (ID: {c.get('id', 'N/A')}, Score: {c.get('score', 0.0):.4f}):\n{c.get('text', '')}"
         for i, c in enumerate(chunks)]
    )
    return "Retrieved Raw Context Snippets:\n" + formatted_chunks

# --- Livestock Breed Retrieval Function ---
def retrieve_livestock_breed_info_tool(query_text: str, k: int = 3) -> str:
    """
    Retrieves relevant text chunks about livestock breeds from the
    BreedEmbeddings container based on semantic similarity.
    """
    if livestock_container_client is None:
        return "Error: Cosmos DB client for livestock breeds not initialized."

    query_embedding_np = get_embedding(query_text)
    if query_embedding_np is None:
        return "Failed to get query embedding. Cannot retrieve livestock breed info."

    query_embedding_list = query_embedding_np.tolist()

    # The vector search query remains the same structure
    query_str = (
        f"SELECT TOP {k} c.id, c.text, VectorDistance(c.embedding, @queryEmbedding) AS score "
        f"FROM c ORDER BY VectorDistance(c.embedding, @queryEmbedding)"
    )
    params = [{"name": "@queryEmbedding", "value": query_embedding_list}]

    chunks = []
    try:
        items = livestock_container_client.query_items(
            query=query_str,
            parameters=params,
            enable_cross_partition_query=True
        )
        for item in items:
            chunks.append({
                "id": item.get("id"),
                "text": item.get("text", ""),
                "score": item.get("score")
            })
    except Exception as e:
        print(f"Unexpected error querying Cosmos DB (livestock breeds): {e}")
        return f"An unexpected error occurred while querying the livestock breeds database: {e}"

    if not chunks:
        return "No relevant information found about livestock breeds for this query."

    formatted_chunks = "\n\n---\n\n".join(
        [f"Snippet {i+1} (ID: {c.get('id', 'N/A')}):\n{c.get('text', '')}"
         for i, c in enumerate(chunks)]
    )
    return "Retrieved Raw Context Snippets about Livestock Breeds:\n" + formatted_chunks


def retrieve_from_chat_history(query_text: str, user_id: str, k: int = 2) -> str:
    """
    Retrieves the most relevant conversation summaries for a specific user from the
    'chat_history' container based on semantic similarity.
    """
    if chat_history_container_client is None:
        return "Error: The client for chat history is not initialized."

    if not user_id:
        return "Error: A user_id must be provided to search chat history."

    # Generate the embedding for the user's query
    query_embedding_np = get_embedding(query_text)
    if query_embedding_np is None:
        return "Failed to get query embedding. Cannot search chat history."

    query_embedding_list = query_embedding_np.tolist()

    # The query now includes a 'WHERE' clause to filter by the specific user_id
    query_str = (
        f"SELECT TOP {k} c.id, c.text, VectorDistance(c.embedding, @queryEmbedding) AS score "
        f"FROM c WHERE c.user_id = @userId "
        f"ORDER BY VectorDistance(c.embedding, @queryEmbedding)"
    )

    # The parameters list now includes both the embedding and the user_id
    params = [
        {"name": "@queryEmbedding", "value": query_embedding_list},
        {"name": "@userId", "value": user_id}
    ]

    chunks = []
    try:
        # Execute the query against the chat_history container
        items = chat_history_container_client.query_items(
            query=query_str,
            parameters=params,
            enable_cross_partition_query=True
        )
        for item in items:
            chunks.append({
                "text": item.get("text", ""),
                "score": item.get("score")
            })

    except Exception as e:
        print(f"An unexpected error occurred while querying chat history: {e}")
        return f"An unexpected error occurred while querying chat history: {e}"

    if not chunks:
        return "No relevant past conversations found in this user's chat history."

    # Format the retrieved chunks into a single string for the agent
    formatted_chunks = "\n\n---\n\n".join(
        [f"Past Conversation Snippet (Score: {c['score']:.4f}):\n{c['text']}" for c in chunks]
    )
    
    return "Retrieved Past Conversation Summaries:\n" + formatted_chunks
# --- Correct Data Ingestion Functions ---

def add_image_reference_to_cosmos(image_bytes: bytes, image_description: str, user_id: str, file_extension: str = 'jpg', metadata: Dict = None) -> Optional[str]:
    """Uploads an image to Blob Storage and stores its reference metadata in Cosmos DB."""
    if not image_bytes or not image_description:
        print("Skipping image storage: Missing image data or description.")
        return None
    try:
        blob_url,unique_image_id = upload_to_blob_storage(blob_service_client, IMAGE_BLOB_CONTAINER_NAME, image_bytes, file_extension)
        embedding = get_embedding(image_description)
        if embedding is None:
            print("Failed to get embedding for image description. Aborting.")
            return None
        doc = {
            "id": unique_image_id, "user_id": user_id, "blob_url": blob_url, "image_description": image_description,
            "text_embedding": embedding.tolist(), "metadata": metadata or {}, "upload_date": datetime.utcnow().isoformat()
        }
        image_embeddings_container_client.upsert_item(body=doc)
        print(f"Successfully saved image reference to Cosmos DB. ID: {unique_image_id}")
        return unique_image_id,blob_url
    except Exception as e:
        print(f"Failed to save image reference: {e}")
        return None

def add_audio_reference_to_cosmos(audio_bytes: bytes, user_id: str, file_extension: str = 'wav', metadata: Dict = None) -> Optional[str]:
    """Transcribes audio, uploads file to Blob, and stores metadata in Cosmos DB."""
    if not audio_bytes:
        print("Skipping audio storage: No audio data provided.")
        return None
    try:
        blob_url = upload_to_blob_storage(blob_service_client, AUDIO_BLOB_CONTAINER_NAME, audio_bytes, file_extension)
        transcription = transcribe_audio_to_text(audio_bytes)
        if not transcription:
            print("Transcription failed. Aborting.")
            return None
        embedding = get_embedding(transcription)
        if embedding is None:
            print("Failed to get embedding for transcription. Aborting.")
            return None
        audio_id = str(uuid.uuid4())
        doc = {
            "id": audio_id, "user_id": user_id, "blob_url": blob_url, "transcription": transcription,
            "text_embedding": embedding.tolist(), "metadata": metadata or {}, "upload_date": datetime.utcnow().isoformat()
        }
        audio_embeddings_container_client.upsert_item(body=doc)
        print(f"Successfully saved audio reference to Cosmos DB. ID: {audio_id}")
        return audio_id
    except Exception as e:
        print(f"Failed to save audio reference: {e}")
        return None

def add_multimodal_memory_to_cosmos(text_to_save: str, user_id: str, image_ids: List[str] = None, audio_ids: List[str] = None) -> bool:
    """Saves a chat message to the 'chat_history' container, linking any media."""
    if not text_to_save and not image_ids and not audio_ids:
        print("Skipping memory storage: No text, image, or audio provided.")
        return False
    embedding = get_embedding(text_to_save) if text_to_save else None
    memory_document = {
        "id": str(uuid.uuid4()), "user_id": user_id, "text": text_to_save,
        "embedding": embedding.tolist() if embedding is not None else None,
        "image_ids": image_ids or [], "audio_ids": audio_ids or [],
        "timestamp": datetime.utcnow().isoformat()
    }


    try:
        chat_history_container_client.upsert_item(body=memory_document)
        print(f"Successfully saved multimodal memory to 'chat_history'. ID: {memory_document['id']}")
        return True
    except Exception as e:
        print(f"Failed to save chat memory: {e}")
        return False

# --- Advanced Retrieval Functions with a critical fix ---

def retrieve_images_by_ids(image_ids: List[str]) -> List[Dict]:
    """Retrieves image details from the image_embeddings container by their IDs."""
    if not image_ids or image_embeddings_container_client is None:
        return []
    retrieved_images = []
    for image_id in image_ids:
        try:
            item = image_embeddings_container_client.read_item(item=image_id, partition_key=image_id)
            retrieved_images.append(item)
        except Exception as e:
            print(f"Error retrieving image {image_id}: {e}")
            continue
    return retrieved_images

def retrieve_images_from_user_history(query_text: str, user_id: str, k: int = 2) -> str:
    """Retrieves relevant images from the user's chat history based on semantic similarity."""
    if chat_history_container_client is None:
        return "Error: Chat history client not initialized."

    query_embedding_np = get_embedding(query_text)
    if query_embedding_np is None:
        return "Failed to get query embedding for image search."

    # --- CRITICAL FIX in the query below ---
    # We query by the length of the image_ids array instead of the non-existent 'has_images' field.
    query_str = (
        f"SELECT TOP {k} c.id, c.text, c.image_ids, VectorDistance(c.embedding, @queryEmbedding) AS score "
        f"FROM c WHERE c.user_id = @userId AND ARRAY_LENGTH(c.image_ids) > 0 "
        f"ORDER BY VectorDistance(c.embedding, @queryEmbedding)"
    )
    params = [{"name": "@queryEmbedding", "value": query_embedding_np.tolist()}, {"name": "@userId", "value": user_id}]

    try:
        items = chat_history_container_client.query_items(query=query_str, parameters=params, enable_cross_partition_query=True)
        image_contexts = []
        all_image_ids = []
        for item in items:
            all_image_ids.extend(item.get("image_ids", []))
        
        if all_image_ids:
            images = retrieve_images_by_ids(list(set(all_image_ids))) # Use set to avoid duplicate lookups
            for img in images:
                image_contexts.append(f"Previous Image Analysis: {img.get('image_description', 'No description.')}")
        
        return "\n".join(image_contexts) if image_contexts else "No relevant previous images found in your history."
    except Exception as e:
        return f"Error retrieving image history: {e}"

def retrieve_multimodal_chunks_tool(query_text: str, user_id: str, k: int = 3) -> str:
    """Enhanced retrieval that considers both text and image context from user's history."""
    text_results = retrieve_semantic_chunks_tool(query_text, user_id, k) # Give full k to text search
    image_results = retrieve_images_from_user_history(query_text, user_id, k) # Also give full k
    combined_results = f"{text_results}\n\n--- IMAGE CONTEXT ---\n{image_results}"
    return combined_results
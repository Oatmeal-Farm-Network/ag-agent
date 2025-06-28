# cosmos_utils.py
# This file is dedicated to functions that interact with Azure Cosmos DB, 
# primarily for performing semantic searches to retrieve relevant data chunks

import traceback
from typing import List, Dict, Optional, Union
import numpy as np
from azure.cosmos import exceptions as CosmosExceptions
import streamlit as st
from config import livestock_container_client,chat_history_container_client, container_client, image_embeddings_container_client
from utilities_module.embedding_utils import get_embedding
import uuid
from datetime import datetime
import base64

# Import from config and utils
from config import container_client, embedding_client # For type hints, though direct use is minimized
from utils import get_embedding
import uuid

# long term memory function
def add_memory_to_cosmos(text_to_save: str,user_id: str) -> bool:
    """
    Embeds a piece of text and saves it as a new item in the 'chat_history' container.
    """
    if not text_to_save or not text_to_save.strip():
        print("Skipping memory storage: No text provided.")
        return False

    # ---  Use the specific client for chat history ---
    if chat_history_container_client is None:
        st.error("Chat history DB client not initialized. Cannot save memory.")
        return False

    # Generates the embedding for the text
    embedding_vector_np = get_embedding(text_to_save)
    if embedding_vector_np is None:
        st.warning("Failed to generate embedding. Memory not saved.")
        return False

    # Prepare the document to be saved
    memory_document = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "text": text_to_save,
        "embedding": embedding_vector_np.tolist()
    }

    #  Save the document to the CHAT HISTORY container
    try:
        # --- Use the specific client for chat history ---
        chat_history_container_client.upsert_item(body=memory_document)
        print(f"Successfully saved memory to 'chat_history' container. ID: {memory_document['id']}")
        st.toast("📝 Learning from this interaction...")
        return True
    except Exception as e:
        print(f"Error saving memory to chat_history container: {e}")
        st.error(f"Failed to save memory to chat_history container: {e}")
        return False

def retrieve_semantic_chunks_tool(query_text: str, user_id, k: int = 3) -> str:
    """
    Retrieves relevant text chunks from Cosmos DB based on semantic similarity.
    This function is designed to be registered as a tool for an AutoGen agent.
    """
    if container_client is None:
        # This check is crucial if container_client is imported and used directly
        st.error("Cosmos DB client not initialized. Cannot retrieve chunks.")
        return "Error: Cosmos DB client not initialized. Cannot retrieve chunks."
    # embedding_client is used via get_embedding, which has its own check.

    query_embedding_np = get_embedding(query_text)
    if query_embedding_np is None:
        # get_embedding will show a Streamlit warning/error
        return "Failed to get query embedding. Cannot retrieve chunks."

    query_embedding_list = query_embedding_np.tolist()

    # Cosmos DB vector search query
    query_str = (
        f"SELECT TOP {k} c.id, c.text, VectorDistance(c.embedding, @queryEmbedding) AS score "
        f"FROM c ORDER BY VectorDistance(c.embedding, @queryEmbedding)"
    )
    params = [{"name": "@queryEmbedding", "value": query_embedding_list}]

    chunks = []
    try:
        items = container_client.query_items(
            query=query_str,
            parameters=params,
            enable_cross_partition_query=True # Set to False if your container is not partitioned or query targets a single partition
        )
        for item in items:
            chunks.append({
                "id": item.get("id"),
                "text": item.get("text", ""),
                "score": item.get("score")
            })
    except CosmosExceptions.CosmosHttpResponseError as e:
        msg = str(e)
        print(f"Cosmos DB HTTP Error: {msg} (Status Code: {e.status_code}, Substatus: {e.sub_status})")
        # Check for common vector index issues
        if e.status_code == 400 and "Invalid query" in msg: # Heuristic for vector index issues
             return f"Error: Cosmos DB query failed. This might be due to a missing vector index or incorrect query syntax. Details: {msg}"
        return f"Error querying Cosmos DB: {msg}"
    except Exception as e:
        print(f"Unexpected error querying Cosmos DB: {e}")
        # traceback.print_exc() # For server-side logging
        return f"An unexpected error occurred while querying Cosmos DB: {e}"

    if not chunks:
        return "No relevant information found in the provided snippets based on the query."

    # Format chunks for display or further processing by an LLM
    formatted_chunks = "\n\n---\n\n".join(
        [f"Snippet {i+1} (ID: {c.get('id', 'N/A')}, Score: {c.get('score', 0.0):.4f}):\n{c.get('text', '')}"
         for i, c in enumerate(chunks)]
    )
    return "Retrieved Raw Context Snippets:\n" + formatted_chunks

# Tool for retrieving livestock breed information 
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
        # --- CRITICAL: Use the new livestock_container_client ---
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




# Function to retrieve conversation summaries from chat history


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
        # In a real app, you might want to log the full traceback
        return f"An unexpected error occurred while querying chat history: {e}"

    if not chunks:
        return "No relevant past conversations found in this user's chat history."

    # Format the retrieved chunks into a single string for the agent
    formatted_chunks = "\n\n---\n\n".join(
        [f"Past Conversation Snippet (Score: {c['score']:.4f}):\n{c['text']}" for c in chunks]
    )
    
    return "Retrieved Past Conversation Summaries:\n" + formatted_chunks

# --- NEW: Image embedding storage function ---
def add_image_to_cosmos(image_data: str, image_description: str, user_id: str, metadata: Dict = None) -> str:
    """
    Stores an image with its description and embeddings in the image_embeddings container.
    Returns the image ID for reference.
    """
    if not image_data or not image_description:
        print("Skipping image storage: Missing image data or description.")
        return None

    # --- Use the specific client for image embeddings ---
    if image_embeddings_container_client is None:
        st.error("Image embeddings DB client not initialized. Cannot save image.")
        return None

    # Generate embedding for the image description
    description_embedding_np = get_embedding(image_description)
    if description_embedding_np is None:
        st.warning("Failed to generate embedding for image description. Image not saved.")
        return None

    # Prepare the image document
    image_id = str(uuid.uuid4())
    image_document = {
        "id": image_id,
        "user_id": user_id,
        "image_data": image_data,  # base64 encoded
        "image_description": image_description,
        "text_embedding": description_embedding_np.tolist(),
        "metadata": metadata or {},
        "upload_date": datetime.utcnow().isoformat()
    }

    # Save the document to the IMAGE EMBEDDINGS container
    try:
        image_embeddings_container_client.upsert_item(body=image_document)
        print(f"Successfully saved image to 'image_embeddings' container. ID: {image_id}")
        return image_id
    except Exception as e:
        print(f"Error saving image to image_embeddings container: {e}")
        st.error(f"Failed to save image to image_embeddings container: {e}")
        return None

# --- NEW: Enhanced memory storage with images ---
def add_multimodal_memory_to_cosmos(text_to_save: str, user_id: str, image_ids: List[str] = None) -> bool:
    """
    Enhanced version of add_memory_to_cosmos that includes image references.
    """
    if not text_to_save or not text_to_save.strip():
        print("Skipping memory storage: No text provided.")
        return False

    # --- Use the specific client for chat history ---
    if chat_history_container_client is None:
        st.error("Chat history DB client not initialized. Cannot save memory.")
        return False

    # Generates the embedding for the text
    embedding_vector_np = get_embedding(text_to_save)
    if embedding_vector_np is None:
        st.warning("Failed to generate embedding. Memory not saved.")
        return False

    # Prepare the enhanced document
    memory_document = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "text": text_to_save,
        "embedding": embedding_vector_np.tolist(),
        "has_images": bool(image_ids),
        "image_count": len(image_ids) if image_ids else 0,
        "image_ids": image_ids or [],
        "timestamp": datetime.utcnow().isoformat()
    }

    # Save the document to the CHAT HISTORY container
    try:
        chat_history_container_client.upsert_item(body=memory_document)
        print(f"Successfully saved multimodal memory to 'chat_history' container. ID: {memory_document['id']}")
        st.toast("📝 Learning from this interaction...")
        return True
    except Exception as e:
        print(f"Error saving multimodal memory to chat_history container: {e}")
        st.error(f"Failed to save multimodal memory to chat_history container: {e}")
        return False

# --- NEW: Retrieve images by IDs ---
def retrieve_images_by_ids(image_ids: List[str]) -> List[Dict]:
    """
    Retrieves images from the image_embeddings container by their IDs.
    """
    if not image_ids or image_embeddings_container_client is None:
        return []

    retrieved_images = []
    for image_id in image_ids:
        try:
            item = image_embeddings_container_client.read_item(
                item=image_id,
                partition_key=image_id
            )
            retrieved_images.append({
                "id": item.get("id"),
                "image_description": item.get("image_description"),
                "metadata": item.get("metadata", {})
            })
        except Exception as e:
            print(f"Error retrieving image {image_id}: {e}")
            continue

    return retrieved_images

# --- NEW: Enhanced retrieval that includes image context ---
def retrieve_multimodal_chunks_tool(query_text: str, user_id: str, k: int = 3) -> str:
    """
    Enhanced retrieval that considers both text and image context from user's history.
    """
    # First, get text-based results
    text_results = retrieve_semantic_chunks_tool(query_text, user_id, k//2)
    
    # Then, get image-based results from user's history
    image_results = retrieve_images_from_user_history(query_text, user_id, k//2)
    
    # Combine results
    combined_results = f"{text_results}\n\n--- IMAGE CONTEXT ---\n{image_results}"
    return combined_results

# --- NEW: Retrieve relevant images from user's history ---
def retrieve_images_from_user_history(query_text: str, user_id: str, k: int = 2) -> str:
    """
    Retrieves relevant images from the user's chat history based on semantic similarity.
    """
    if chat_history_container_client is None:
        return "Error: Chat history client not initialized."

    # Get embedding for the query
    query_embedding_np = get_embedding(query_text)
    if query_embedding_np is None:
        return "Failed to get query embedding for image search."

    query_embedding_list = query_embedding_np.tolist()

    # Query for chat history entries that have images
    query_str = (
        f"SELECT TOP {k} c.id, c.text, c.image_ids, VectorDistance(c.embedding, @queryEmbedding) AS score "
        f"FROM c WHERE c.user_id = @userId AND c.has_images = true "
        f"ORDER BY VectorDistance(c.embedding, @queryEmbedding)"
    )
    
    params = [
        {"name": "@queryEmbedding", "value": query_embedding_list},
        {"name": "@userId", "value": user_id}
    ]

    try:
        items = chat_history_container_client.query_items(
            query=query_str,
            parameters=params,
            enable_cross_partition_query=True
        )
        
        image_contexts = []
        for item in items:
            image_ids = item.get("image_ids", [])
            if image_ids:
                # Retrieve the actual image descriptions
                images = retrieve_images_by_ids(image_ids)
                for img in images:
                    image_contexts.append(f"Previous Image Analysis: {img['image_description']}")
        
        if image_contexts:
            return "\n".join(image_contexts)
        else:
            return "No relevant previous images found in your history."
            
    except Exception as e:
        print(f"Error retrieving images from user history: {e}")
        return f"Error retrieving image history: {e}"


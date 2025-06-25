# cosmos_utils.py
# This file is dedicated to functions that interact with Azure Cosmos DB, 
# primarily for performing semantic searches to retrieve relevant data chunks

import traceback
from typing import List, Dict, Optional
import numpy as np
from azure.cosmos import exceptions as CosmosExceptions
import streamlit as st
from config import livestock_container_client,chat_history_container_client, container_client
from utilities_module.embedding_utils import get_embedding
import uuid

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


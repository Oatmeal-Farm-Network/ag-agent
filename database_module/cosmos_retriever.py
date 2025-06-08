# cosmos_utils.py
# This file is dedicated to functions that interact with Azure Cosmos DB, 
# primarily for performing semantic searches to retrieve relevant data chunks

import traceback
from typing import List, Dict, Optional
import numpy as np
from azure.cosmos import exceptions as CosmosExceptions
import streamlit as st
from config import container_client, livestock_container_client
from utilities_module.embedding_utils import get_embedding

# Import from config and utils
from config import container_client, embedding_client # For type hints, though direct use is minimized
from utils import get_embedding

def retrieve_semantic_chunks_tool(query_text: str, k: int = 3) -> str:
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
# knowledge_retriever.py

import os
import httpx
import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

from azure.core.credentials import AzureKeyCredential
from azure.search.documents.aio import SearchClient
from azure.search.documents.models import VectorizedQuery

# --- 1. Initialize FastAPI App ---

app = FastAPI(
    title="Knowledge Retrieval Agent API",
    description="A service for advanced, multi-index document retrieval from the agriculture knowledge base.",
    version="1.1.0"
)

# --- 2. Load Configuration from Environment Variables ---

AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_KEY = os.getenv("AZURE_SEARCH_KEY")
# Expects a comma-separated string, e.g., "index1,index2,index3"
AZURE_SEARCH_INDEX_NAMES_STR = os.getenv("KNOWLEDGE_BASE_INDEX_NAMES")

AZURE_OPENAI_EMBEDDING_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")

# --- 3. Define API Data Models (Pydantic) ---

class RetrievalRequest(BaseModel):
    query: str = Field(..., description="The user's natural language query.")
    user_id: str = Field(..., description="The unique ID of the user for session-specific searches.")
    top_k: int = Field(5, description="The final number of documents to return.")
    filters: Optional[Dict[str, Any]] = Field(None, description="Key-value pairs for metadata filtering.")

class Document(BaseModel):
    content: str
    metadata: Dict[str, Any]
    score: float

class RetrievalResponse(BaseModel):
    retrieved_documents: List[Document]


# --- 4. Helper function to generate embeddings ---

async def get_embedding(text: str) -> List[float]:
    """Generates embeddings for a query using Azure OpenAI."""
    # This check is important for startup and error handling
    if not all([AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_EMBEDDING_DEPLOYMENT, AZURE_OPENAI_KEY]):
        raise HTTPException(status_code=503, detail="Service Unavailable: Azure OpenAI environment variables not set.")
        
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{AZURE_OPENAI_ENDPOINT}/openai/deployments/{AZURE_OPENAI_EMBEDDING_DEPLOYMENT}/embeddings?api-version=2023-05-15",
            headers={"api-key": AZURE_OPENAI_KEY, "Content-Type": "application/json"},
            json={"input": text}
        )
        response.raise_for_status()
        return response.json()["data"][0]["embedding"]

# --- 5. API Endpoint for Multi-Index Search ---

@app.post("/retrieve", response_model=RetrievalResponse)
async def retrieve_knowledge_endpoint(request: RetrievalRequest):
    """
    API endpoint to retrieve documents by searching across multiple indexes in parallel.
    """
    if not all([AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_KEY, AZURE_SEARCH_INDEX_NAMES_STR]):
        raise HTTPException(status_code=503, detail="Service Unavailable: Azure AI Search environment variables not set.")

    try:
        # 1. Get the list of index names from the environment variable
        index_names = [name.strip() for name in AZURE_SEARCH_INDEX_NAMES_STR.split(',')]
        
        # 2. Generate the query vector once
        query_vector = await get_embedding(request.query)
        vector_query = VectorizedQuery(vector=query_vector, k_nearest_neighbors=request.top_k, fields="contentVector")

        # 3. Create a search task for each index
        tasks = []
        for index_name in index_names:
            search_client = SearchClient(
                endpoint=AZURE_SEARCH_ENDPOINT,
                index_name=index_name,
                credential=AzureKeyCredential(AZURE_SEARCH_KEY)
            )
            # We create an async task to search a single index
            task = asyncio.create_task(
                search_client.search(
                    search_text=request.query,
                    vector_queries=[vector_query],
                    select=["content", "metadata", "id"],
                    top=request.top_k
                )
            )
            tasks.append(task)

        # 4. Run all search tasks in parallel
        results_from_all_indexes = await asyncio.gather(*tasks, return_exceptions=True)

        # 5. Collect, merge, and rank all results
        combined_results = []
        for result_set in results_from_all_indexes:
            if isinstance(result_set, Exception):
                print(f"Warning: A search task failed with exception: {result_set}")
                continue # Skip failed tasks
            
            async for result in result_set:
                combined_results.append(result)
        
        # Sort all collected documents by their relevance score
        sorted_results = sorted(combined_results, key=lambda x: x['@search.score'], reverse=True)
        
        # 6. Format the top K results for the final response
        final_docs = sorted_results[:request.top_k]
        response_docs = [
            Document(
                content=doc.get("content", ""),
                metadata=doc.get("metadata", {}),
                score=doc["@search.score"]
            ) for doc in final_docs
        ]
            
        return RetrievalResponse(retrieved_documents=response_docs)

    except Exception as e:
        print(f"An error occurred during the multi-index retrieval: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error during retrieval process.")
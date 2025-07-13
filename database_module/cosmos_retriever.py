# database_module/cosmos_retriever.py
# This file is dedicated to functions that perform semantic searches using LangChain.

from memory_module.langchain_setup import vector_store, livestock_vector_store

def retrieve_knowledge_base_tool(query_text: str, k: int = 3) -> str:
    """
    Searches the general knowledge base (RAG documents) for relevant information.
    This search is public and not user-specific.
    """
    try:
        results = vector_store.similarity_search(query=query_text, k=k)
        if not results:
            return "No relevant information found in the knowledge base."
        
        # Combine the content of the found documents
        formatted_results = "\\n\\n---\\n\\n".join([doc.page_content for doc in results])
        return f"Context from Knowledge Base:\\n{formatted_results}"
    except Exception as e:
        return f"An error occurred while querying the knowledge base: {e}"

def retrieve_user_memory_tool(query_text: str, user_id: str, k: int = 3) -> str:
    """
    Retrieves the most relevant long-term memories for a SPECIFIC user.
    """
    try:
        # Note: As of some versions, LangChain's Cosmos DB integration might not support metadata filtering.
        # A common workaround is to include the user_id in the search query itself to leverage semantic context.
        contextual_query = f"From the memory of user {user_id}: {query_text}"
        results = vector_store.similarity_search(query=contextual_query, k=k)
        
        if not results:
            return "No relevant personal memories found."

        formatted_results = "\\n\\n---\\n\\n".join([doc.page_content for doc in results])
        return f"Context from Personal Memories:\\n{formatted_results}"
    except Exception as e:
        return f"An error occurred while querying user memories: {e}"

def retrieve_livestock_breed_info_tool(query_text: str, k: int = 3) -> str:
    """
    Retrieves information about livestock breeds from its specialized vector store.
    """
    try:
        results = livestock_vector_store.similarity_search(query=query_text, k=k)
        if not results:
            return "No relevant information found about livestock breeds."

        formatted_results = "\\n\\n---\\n\\n".join([doc.page_content for doc in results])
        return f"Context from Livestock Breed Knowledge Base:\\n{formatted_results}"
    except Exception as e:
        return f"An error occurred while querying the livestock breeds database: {e}"
# memory_module/langchain_setup.py 
from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.vectorstores import AzureCosmosDBNoSqlVectorSearch
from langchain_community.chat_message_histories import CosmosDBChatMessageHistory
from azure.cosmos import CosmosClient, PartitionKey
import os

# Import the variables from your main config file
from config import (
    AZURE_OPENAI_API_KEY_VAL, AZURE_OPENAI_ENDPOINT_VAL, AZURE_OPENAI_API_VERSION_VAL, 
    EMBED_DEPLOYMENT, DATABASE_NAME, CONTAINER_NAME,
    CHAT_HISTORY_CONTAINER_NAME, LIVESTOCK_CONTAINER_NAME
)

# 1. Initialize the Embeddings Model
embeddings = AzureOpenAIEmbeddings(
    model=EMBED_DEPLOYMENT,
    api_key=AZURE_OPENAI_API_KEY_VAL,
    api_version=AZURE_OPENAI_API_VERSION_VAL,
    azure_endpoint=AZURE_OPENAI_ENDPOINT_VAL
)

# 2. Define required policies for Cosmos DB NoSQL
vector_embedding_policy = {
    "vectorEmbeddings": [{"path": "/embedding", "dataType": "float32", "distanceFunction": "cosine", "dimensions": 1536}]
}
indexing_policy = {
    "indexingMode": "consistent", 
    "includedPaths": [{"path": "/*"}], 
    "excludedPaths": [{"path": '/"_etag"/?'}],
    "vectorIndexes": [{"path": "/embedding", "type": "diskANN"}]
}
cosmos_container_properties = {"partition_key": PartitionKey(path="/id")}
cosmos_database_properties = {}  # Add any database-specific properties if needed

# 3. Create Cosmos Client
cosmos_client = CosmosClient(
    url=os.getenv("COSMOS_ENDPOINT"),
    credential=os.getenv("COSMOS_KEY")
)

# 4. Initialize the Cosmos DB Vector Stores for Long-Term Memory
# Main vector store
vector_store = AzureCosmosDBNoSqlVectorSearch(
    cosmos_client=cosmos_client,
    database_name=DATABASE_NAME,
    container_name=CONTAINER_NAME,
    embedding=embeddings,
    vector_embedding_policy=vector_embedding_policy,
    indexing_policy=indexing_policy,
    cosmos_container_properties=cosmos_container_properties,
    cosmos_database_properties=cosmos_database_properties
)

# Livestock vector store
livestock_vector_store = AzureCosmosDBNoSqlVectorSearch(
    cosmos_client=cosmos_client,
    database_name=DATABASE_NAME,
    container_name=LIVESTOCK_CONTAINER_NAME,
    embedding=embeddings,
    vector_embedding_policy=vector_embedding_policy,
    indexing_policy=indexing_policy,
    cosmos_container_properties=cosmos_container_properties,
    cosmos_database_properties=cosmos_database_properties
)

# 5. Define a function to get Chat History for Short-Term Memory
def get_session_history(session_id: str, user_id: str) -> CosmosDBChatMessageHistory:
    """Gets a chat history object for a specific session, managed by LangChain."""
    history = CosmosDBChatMessageHistory(
        cosmos_endpoint=os.getenv("COSMOS_ENDPOINT"),
        cosmos_database=DATABASE_NAME,
        cosmos_container=CHAT_HISTORY_CONTAINER_NAME,
        session_id=session_id,
        user_id=user_id,
        credential=os.getenv("COSMOS_KEY")
    )
    # Ensure the database and container are ready
    history.prepare_cosmos()
    return history

print("✅ LangChain components initialized successfully.")
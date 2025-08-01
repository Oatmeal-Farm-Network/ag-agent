# config.py
import os
import sys
from dotenv import load_dotenv
from mem0 import Memory
from azure.storage.blob import BlobServiceClient
from azure.cosmos import CosmosClient, exceptions as CosmosExceptions

# Load environment variables from .env file
load_dotenv()

print("--- Initializing Application Configuration ---")

# --- Set Prefixed Environment Variables for Mem0 ---
# This ensures the mem0 library automatically finds the correct credentials.
os.environ["EMBEDDING_AZURE_OPENAI_API_KEY"] = os.getenv("AZURE_OPENAI_API_KEY")
os.environ["EMBEDDING_AZURE_ENDPOINT"] = os.getenv("AZURE_OPENAI_API_BASE")
os.environ["EMBEDDING_AZURE_DEPLOYMENT"] = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
os.environ["EMBEDDING_AZURE_API_VERSION"] = os.getenv("AZURE_OPENAI_API_VERSION")

os.environ["LLM_AZURE_OPENAI_API_KEY"] = os.getenv("AZURE_OPENAI_API_KEY")
os.environ["LLM_AZURE_ENDPOINT"] = os.getenv("AZURE_OPENAI_API_BASE")
os.environ["LLM_AZURE_DEPLOYMENT"] = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME")
os.environ["LLM_AZURE_API_VERSION"] = os.getenv("AZURE_OPENAI_API_VERSION")
print("✅ Prefixed environment variables set for Mem0.")


# --- Configuration Variables from .env ---
AZURE_AI_SEARCH_SERVICE_NAME = os.getenv("AZURE_AI_SEARCH_SERVICE_NAME")
AZURE_AI_SEARCH_API_KEY = os.getenv("AZURE_AI_SEARCH_API_KEY")
EMBED_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
CHAT_DEPLOYMENT = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME")
BLOB_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
IMAGE_BLOB_CONTAINER_NAME = "images"
AUDIO_BLOB_CONTAINER_NAME = "audio"


# --- Mem0 Client Initialization ---
# This is now the single source for all memory operations.
mem0_config = {
    "vector_store": {
        "provider": "azure_ai_search",
        "config": {
            "service_name": AZURE_AI_SEARCH_SERVICE_NAME,
            "api_key": AZURE_AI_SEARCH_API_KEY,
            "collection_name": "chat-context-index", # Using your descriptive name
            "embedding_model_dims": 1536
        }
    },
    "embedder": {
        "provider": "azure_openai",
        "config": { "model": EMBED_DEPLOYMENT }
    },
    "llm": {
        "provider": "azure_openai",
        "config": { "model": CHAT_DEPLOYMENT }
    }
}

try:
    memory_client = Memory.from_config(mem0_config)
    print("✅ Mem0 client initialized successfully.")
except Exception as e:
    print(f"❌ Failed to initialize Mem0 client: {e}")
    sys.exit(1)


# --- Azure Blob Storage Client Initialization ---
# We keep this for uploading raw image/audio files.
try:
    if not BLOB_CONNECTION_STRING:
        raise ValueError("AZURE_STORAGE_CONNECTION_STRING not set.")
    blob_service_client = BlobServiceClient.from_connection_string(BLOB_CONNECTION_STRING)
    print("✅ Azure Blob Storage client initialized successfully.")
except Exception as e:
    print(f"❌ Failed to connect to Azure Blob Storage: {e}")
    sys.exit(1)


# --- Autogen and Agent Configuration ---
# This section remains for your application layer.
autogen_llm_config_list = [{
    "model": CHAT_DEPLOYMENT,
    "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
    "base_url": os.getenv("AZURE_OPENAI_API_BASE"),
    "api_type": "azure",
    "api_version": os.getenv("AZURE_OPENAI_API_VERSION"),
}]

# Agent Names
USER_PROXY_NAME = "Farmer_Query_Relay"
SEARCHER_NAME = "SemanticSearcher"
PROCESSOR_NAME = "ContextProcessor"
SOIL_NAME = "SoilScienceSpecialist"
NUTRITION_NAME = "PlantNutritionExpert"
EXPERT_ADVISOR_NAME = "LeadAgriculturalAdvisor"
LIVESTOCK_BREED_NAME = "LivestockBreedSpecialist"
WEATHER_NAME = "WeatherSpecialist"
USERDATAAGENT_NAME = "UserDataAgent"

COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT")
COSMOS_KEY = os.getenv("COSMOS_KEY")
DATABASE_NAME = "OatmealAI"
CONVERSATIONS_HISTORY_CONTAINER_NAME = "conversation_history"

try:
    conversations_history_container_client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)\
        .get_database_client(DATABASE_NAME)\
        .get_container_client(CONVERSATIONS_HISTORY_CONTAINER_NAME)
except Exception as e:
    print("Connection failed:", e)
    conversations_history_container_client = None
# migrate_knowledge.py
import os
from mem0 import Memory
from azure.cosmos import CosmosClient
from dotenv import load_dotenv

# Load environment from .env file
load_dotenv()
print("--- Starting Knowledge Base Migration ---")

# --- Initialize NEW Mem0 Client ---
# Set Prefixed Environment Variables for BOTH Embedder and LLM
os.environ["EMBEDDING_AZURE_OPENAI_API_KEY"] = os.getenv("AZURE_OPENAI_API_KEY")
os.environ["EMBEDDING_AZURE_ENDPOINT"] = os.getenv("AZURE_OPENAI_API_BASE")
os.environ["EMBEDDING_AZURE_DEPLOYMENT"] = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
os.environ["EMBEDDING_AZURE_API_VERSION"] = os.getenv("AZURE_OPENAI_API_VERSION")

os.environ["LLM_AZURE_OPENAI_API_KEY"] = os.getenv("AZURE_OPENAI_API_KEY")
os.environ["LLM_AZURE_ENDPOINT"] = os.getenv("AZURE_OPENAI_API_BASE")
os.environ["LLM_AZURE_DEPLOYMENT"] = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME")
os.environ["LLM_AZURE_API_VERSION"] = os.getenv("AZURE_OPENAI_API_VERSION")
print("✅ Prefixed environment variables set for Mem0.")

# Complete mem0 config
mem0_config = {
    "vector_store": {
        "provider": "azure_ai_search",
        "config": {
            "service_name": os.getenv("AZURE_AI_SEARCH_SERVICE_NAME"),
            "api_key": os.getenv("AZURE_AI_SEARCH_API_KEY"),
            "collection_name": "mem0_migrate_cosmosdb_breedembeddings", 
            "embedding_model_dims": 1536
        }
    },
    "embedder": { 
        "provider": "azure_openai", 
        "config": { "model": os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT") } 
    },
    "llm": {
        "provider": "azure_openai",
        "config": { "model": os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME") }
    }
}
memory_client = Memory.from_config(mem0_config)
print("✅ Initialized Mem0 client.")


# --- Initialize OLD Cosmos DB Clients ---
COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT")
COSMOS_KEY = os.getenv("COSMOS_KEY")
DATABASE_NAME = "OatmealAI"

cosmos_db_client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
database_client = cosmos_db_client.get_database_client(DATABASE_NAME)
livestock_container_client = database_client.get_container_client("BreedEmbeddings")
print("✅ Initialized Cosmos DB clients.")

# --- Migration Logic ---
def migrate_container(container_client, source_name):
    print(f"\nMigrating data from '{source_name}' container...")
    try:
        items = list(container_client.query_items(query="SELECT * FROM c", enable_cross_partition_query=True))
        if not items:
            print(f"No items found in '{source_name}' to migrate.")
            return

        print(f"Found {len(items)} items to migrate.")
        for item in items:
            text_to_migrate = item.get('CombinedText')
            if text_to_migrate:
                print(f"  -> Adding: '{text_to_migrate[:50]}...'")
                memory_client.add(text_to_migrate, user_id="knowledge_base_user")
            else:
                print(f"  -> Skipping item {item.get('id')} (no 'text' field).")
        print(f"✅ Finished migrating '{source_name}'.")

    except Exception as e:
        print(f"❌ An error occurred during migration of '{source_name}': {e}")

# Run the migration for ONLY the livestock container
migrate_container(livestock_container_client, "BreedEmbeddings")

print("\n--- Migration Complete ---")
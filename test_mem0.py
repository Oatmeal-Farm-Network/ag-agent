from dotenv import load_dotenv
import os
from mem0 import Memory

# Load environment variables from .env file
load_dotenv()

print("--- Testing Mem0 with Azure AI Search ---")

# --- Set Prefixed Environment Variables ---
os.environ["EMBEDDING_AZURE_OPENAI_API_KEY"] = os.getenv("AZURE_OPENAI_API_KEY")
os.environ["EMBEDDING_AZURE_ENDPOINT"] = os.getenv("AZURE_OPENAI_API_BASE")
os.environ["EMBEDDING_AZURE_DEPLOYMENT"] = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
os.environ["EMBEDDING_AZURE_API_VERSION"] = os.getenv("AZURE_OPENAI_API_VERSION")

os.environ["LLM_AZURE_OPENAI_API_KEY"] = os.getenv("AZURE_OPENAI_API_KEY")
os.environ["LLM_AZURE_ENDPOINT"] = os.getenv("AZURE_OPENAI_API_BASE")
os.environ["LLM_AZURE_DEPLOYMENT"] = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME")
os.environ["LLM_AZURE_API_VERSION"] = os.getenv("AZURE_OPENAI_API_VERSION")
print("✅ Prefixed environment variables set for Embedder and LLM.")


# --- Configuration Variables ---
AZURE_AI_SEARCH_SERVICE_NAME = os.getenv("AZURE_AI_SEARCH_SERVICE_NAME")
AZURE_AI_SEARCH_API_KEY = os.getenv("AZURE_AI_SEARCH_API_KEY")
EMBED_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
CHAT_DEPLOYMENT = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME")
COLLECTION_NAME = os.getenv("AZURE_AI_SEARCH_INDEX_NAME")


# --- Mem0 Config ---
mem0_config = {
    "vector_store": {
        "provider": "azure_ai_search",
        "config": {
            "service_name": AZURE_AI_SEARCH_SERVICE_NAME,
            "api_key": AZURE_AI_SEARCH_API_KEY,
            "collection_name": COLLECTION_NAME, 
            "embedding_model_dims": 1536
        }
    },
    "embedder": {
        "provider": "azure_openai",
        "config": {
            "model": EMBED_DEPLOYMENT,
        }
    },
    "llm": {
        "provider": "azure_openai",
        "config": {
            "model": CHAT_DEPLOYMENT,
        }
    }
}

# --- Test Logic ---
if CHAT_DEPLOYMENT:
    try:
        memory = Memory.from_config(mem0_config)
        print("✅ Mem0 client initialized successfully with all components.")
        
        # Add a simple string memory
        test_user_id = "test_user_final_123"
        test_memory_text = "The user's favorite city is Paris, and they dislike thrillers."
        
        print(f"\n🧠 Adding SIMPLE Memory: '{test_memory_text}'")
        memory.add(test_memory_text, user_id=test_user_id)
        
        # Search for the memory
        search_query = "What is the user's favorite city?"
        print(f"\n🔍 Searching for: '{search_query}'")
        search_results = memory.search(search_query, user_id=test_user_id)
        
        # --- KEY CHANGE: Print the raw search result object ---
        print("\n✅ Raw Search Results Object:")
        print(search_results)

        if search_results and 'results' in search_results:
            for result in search_results['results']:
                print(f"  - Found: '{result['memory']}' (Score: {result['score']:.4f})")
            
    except Exception as e:
        print(f"\n❌ An error occurred during the test: {e}")
else:
    print("❌ AZURE_OPENAI_CHAT_DEPLOYMENT_NAME not found in .env file.")
#config.py
# This file is responsible for loading environment variables and initializing service clients/configurations.


import os
import streamlit as st
from dotenv import load_dotenv
from openai import AzureOpenAI as SdkAzureOpenAI
from azure.cosmos import CosmosClient, exceptions as CosmosExceptions

# Load environment variables from .env file
load_dotenv()

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT_VAL = os.getenv("AZURE_OPENAI_API_BASE")
key_raw = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_API_KEY_VAL = key_raw.strip() if key_raw else None
AZURE_OPENAI_API_VERSION_VAL = os.getenv("AZURE_OPENAI_API_VERSION")
CHAT_DEPLOYMENT = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME")
EMBED_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")

# Validate Azure OpenAI Environment Variables
if not all([AZURE_OPENAI_ENDPOINT_VAL, AZURE_OPENAI_API_KEY_VAL, AZURE_OPENAI_API_VERSION_VAL, EMBED_DEPLOYMENT, CHAT_DEPLOYMENT]):
    st.error("Azure OpenAI environment variables not fully set. Please check your .env file or environment configuration.")
    st.stop()

# Autogen LLM Configuration List
autogen_llm_config_list = [{
    "model": CHAT_DEPLOYMENT,
    "api_key": AZURE_OPENAI_API_KEY_VAL,
    "base_url": AZURE_OPENAI_ENDPOINT_VAL,
    "api_type": "azure",
    "api_version": AZURE_OPENAI_API_VERSION_VAL,
}]

# Initialize Azure OpenAI Client for Embeddings
embedding_client = None
try:
    embedding_client = SdkAzureOpenAI(
        api_key=AZURE_OPENAI_API_KEY_VAL,
        api_version=AZURE_OPENAI_API_VERSION_VAL,
        azure_endpoint=AZURE_OPENAI_ENDPOINT_VAL
    )
except Exception as e:
    st.error(f"Error initializing AzureOpenAI client for embeddings: {e}")
    st.exception(e)
    st.stop()

# Cosmos DB Configuration
COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT")
COSMOS_KEY = os.getenv("COSMOS_KEY")
DATABASE_NAME = "OatmealAI"  # database name in cosmos db
CONTAINER_NAME = "rag_vectors" #embeddings of intial documents container  in cosmos db
LIVESTOCK_CONTAINER_NAME = "BreedEmbeddings" # Embeddings of livestock breeds container  in cosmos db
CHAT_HISTORY_CONTAINER_NAME = "chat_history" # Container for chat history
IMAGE_EMBEDDINGS_CONTAINER_NAME = "image_embeddings" # Container for image embeddings

# Validate Cosmos DB Environment Variables
if not all([COSMOS_ENDPOINT, COSMOS_KEY]):
    st.error("COSMOS_ENDPOINT or COSMOS_KEY not set. Please check your .env file or environment configuration.")
    st.stop()

# Initialize Cosmos DB Client
container_client = None
try:
    cosmos_db_client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
    database_client = cosmos_db_client.get_database_client(DATABASE_NAME)
    container_client = database_client.get_container_client(CONTAINER_NAME)
    # Test connection (optional, but good for immediate feedback)
    database_client.read()
    container_client.read()
    print("Successfully connected to Cosmos DB.")
except CosmosExceptions.CosmosResourceNotFoundError:
    st.error(f"Cosmos DB database '{DATABASE_NAME}' or container '{CONTAINER_NAME}' not found. Please ensure they exist.")
    st.stop()
except Exception as e:
    st.error(f"Failed to connect to Cosmos DB: {e}")
    st.exception(e)
    st.stop()

# Agent Names (centralized for consistency)
USER_PROXY_NAME = "Farmer_Query_Relay"
SEARCHER_NAME = "SemanticSearcher"
PROCESSOR_NAME = "ContextProcessor"
SOIL_NAME = "SoilScienceSpecialist"
NUTRITION_NAME = "PlantNutritionExpert"
EXPERT_ADVISOR_NAME = "LeadAgriculturalAdvisor"
LIVESTOCK_BREED_NAME = "LivestockBreedSpecialist"
WEATHER_NAME = "WeatherSpecialist" # New agent for weather data


#  Configuration for the Livestock Breed Container 
livestock_container_client = None
try:
    livestock_container_client = database_client.get_container_client(LIVESTOCK_CONTAINER_NAME)
    # Test connection (optional, but good for immediate feedback)
    livestock_container_client.read()
    print(f"Successfully connected to Cosmos DB container: {LIVESTOCK_CONTAINER_NAME}")
except Exception as e:
    st.error(f"Failed to connect to Cosmos DB container '{LIVESTOCK_CONTAINER_NAME}': {e}")
    st.exception(e)



# Configuration for the Chat History Container
chat_history_container_client = None
try:
    # Use the existing database_client to get the new container client
    chat_history_container_client = database_client.get_container_client(CHAT_HISTORY_CONTAINER_NAME)
    
    # Test connection to the new container
    chat_history_container_client.read()
    print(f"Successfully connected to Cosmos DB container: {CHAT_HISTORY_CONTAINER_NAME}")

except CosmosExceptions.CosmosResourceNotFoundError:
    # This error will trigger if you haven't created the container in the Azure Portal yet
    st.error(f"Cosmos DB container '{CHAT_HISTORY_CONTAINER_NAME}' not found. Please ensure it has been created in the Azure Portal.")
    st.stop()
except Exception as e:
    st.error(f"Failed to connect to Cosmos DB container '{CHAT_HISTORY_CONTAINER_NAME}': {e}")
    st.exception(e)
    # st.stop() # You might want to comment out st.stop() if this container is optional
    

# Configuration for the Image Embeddings Container
image_embeddings_container_client = None
try:
    # Use the existing database_client to get the new container client
    image_embeddings_container_client = database_client.get_container_client(IMAGE_EMBEDDINGS_CONTAINER_NAME)
    
    # Test connection to the new container
    image_embeddings_container_client.read()
    print(f"Successfully connected to Cosmos DB container: {IMAGE_EMBEDDINGS_CONTAINER_NAME}")

except CosmosExceptions.CosmosResourceNotFoundError:
    # This error will trigger if you haven't created the container in the Azure Portal yet
    st.error(f"Cosmos DB container '{IMAGE_EMBEDDINGS_CONTAINER_NAME}' not found. Please ensure it has been created in the Azure Portal.")
    st.stop()
except Exception as e:
    st.error(f"Failed to connect to Cosmos DB container '{IMAGE_EMBEDDINGS_CONTAINER_NAME}': {e}")
    st.exception(e)
    st.stop()
    

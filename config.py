# config.py
# This file is responsible for loading environment variables and initializing service clients.

import os
import streamlit as st
from dotenv import load_dotenv
from openai import AzureOpenAI as SdkAzureOpenAI
from azure.cosmos import CosmosClient, exceptions as CosmosExceptions
from azure.storage.blob import BlobServiceClient
from azure.cosmos import CosmosClient
import azure.cognitiveservices.speech as speechsdk





# Load environment variables from .env file
load_dotenv()

## -----------------------------------------------------------------------------
## Azure OpenAI Configuration
## -----------------------------------------------------------------------------
AZURE_OPENAI_ENDPOINT_VAL = os.getenv("AZURE_OPENAI_API_BASE")
key_raw = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_API_KEY_VAL = key_raw.strip() if key_raw else None
AZURE_OPENAI_API_VERSION_VAL = os.getenv("AZURE_OPENAI_API_VERSION")
CHAT_DEPLOYMENT = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME")
EMBED_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")




# Validate Azure OpenAI Environment Variables
if not all([AZURE_OPENAI_ENDPOINT_VAL, AZURE_OPENAI_API_KEY_VAL, AZURE_OPENAI_API_VERSION_VAL, EMBED_DEPLOYMENT, CHAT_DEPLOYMENT]):
    st.error("Azure OpenAI environment variables not fully set. Please check your .env file.")
    st.stop()

# Initialize Azure OpenAI Client for Embeddings
try:
    embedding_client = SdkAzureOpenAI(
        api_key=AZURE_OPENAI_API_KEY_VAL,
        api_version=AZURE_OPENAI_API_VERSION_VAL,
        azure_endpoint=AZURE_OPENAI_ENDPOINT_VAL
    )
except Exception as e:
    st.error(f"Error initializing AzureOpenAI client: {e}")
    st.exception(e)
    st.stop()

## -----------------------------------------------------------------------------
## Azure AI Speech Configuration
## -----------------------------------------------------------------------------
SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION")

if not all([SPEECH_KEY, SPEECH_REGION]):
    # Use a more generic error message if not in a Streamlit context
    print("ERROR: Azure AI Speech environment variables not fully set.")
    # In a real app, you might raise an exception here
    # raise ValueError("Azure AI Speech environment variables not fully set.")
    
# Initialize Speech Config
try:
    speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
    print("Successfully configured Azure AI Speech.")
except Exception as e:
    print(f"ERROR: Failed to configure Azure AI Speech: {e}")
    # raise e

## -----------------------------------------------------------------------------
## Cosmos DB Configuration
## -----------------------------------------------------------------------------
COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT")
COSMOS_KEY = os.getenv("COSMOS_KEY")
DATABASE_NAME = "OatmealAI"
CONTAINER_NAME = "rag_vectors"
LIVESTOCK_CONTAINER_NAME = "BreedEmbeddings"
CHAT_HISTORY_CONTAINER_NAME = "session_metadata"
IMAGE_EMBEDDINGS_CONTAINER_NAME = "image_embeddings"
AUDIO_EMBEDDINGS_CONTAINER_NAME = "audio_embeddings"
cosmos_db_client = CosmosClient(url=COSMOS_ENDPOINT, credential=COSMOS_KEY)
# Validate Cosmos DB Environment Variables
if not all([COSMOS_ENDPOINT, COSMOS_KEY]):
    st.error("COSMOS_ENDPOINT or COSMOS_KEY not set. Please check your .env file.")
    st.stop()

# Helper function to initialize container clients cleanly
def get_container(db_client, container_name):
    try:
        container = db_client.get_container_client(container_name)
        container.read()
        print(f"Successfully connected to Cosmos DB container: '{container_name}'")
        return container
    except CosmosExceptions.CosmosResourceNotFoundError:
        st.error(f"Cosmos DB container '{container_name}' not found. Please ensure it has been created in the Azure Portal.")
        st.stop()
    except Exception as e:
        st.error(f"Failed to connect to Cosmos DB container '{container_name}': {e}")
        st.exception(e)
        st.stop()

# Initialize Cosmos DB Client and all container clients
try:
    cosmos_db_client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
    database_client = cosmos_db_client.get_database_client(DATABASE_NAME)
    database_client.read()
    print("Successfully connected to Cosmos DB database.")
    
    # Initialize all container clients using the helper function
    container_client = get_container(database_client, CONTAINER_NAME)
    livestock_container_client = get_container(database_client, LIVESTOCK_CONTAINER_NAME)
    chat_history_container_client = get_container(database_client, CHAT_HISTORY_CONTAINER_NAME)
    image_embeddings_container_client = get_container(database_client, IMAGE_EMBEDDINGS_CONTAINER_NAME)
    audio_embeddings_container_client = get_container(database_client, AUDIO_EMBEDDINGS_CONTAINER_NAME)

except Exception as e:
    st.error(f"Failed to connect to Cosmos DB: {e}")
    st.exception(e)
    st.stop()

## -----------------------------------------------------------------------------
## Azure Blob Storage Configuration
## -----------------------------------------------------------------------------
BLOB_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
IMAGE_BLOB_CONTAINER_NAME = "images"
AUDIO_BLOB_CONTAINER_NAME = "audio"
CHAT_LOG_BLOB_CONTAINER_NAME = "chatlogs"

# Validate Blob Storage Environment Variable
if not BLOB_CONNECTION_STRING:
    st.error("AZURE_STORAGE_CONNECTION_STRING not set. Please check your .env file.")
    st.stop()
    
# Initialize Blob Service Client
try:
    blob_service_client = BlobServiceClient.from_connection_string(BLOB_CONNECTION_STRING)
    print("Successfully connected to Azure Blob Storage.")
except Exception as e:
    st.error(f"Failed to connect to Azure Blob Storage: {e}")
    st.exception(e)
    st.stop()

## -----------------------------------------------------------------------------
## Autogen and Agent Configuration
## -----------------------------------------------------------------------------
autogen_llm_config_list = [{
    "model": CHAT_DEPLOYMENT,
    "api_key": AZURE_OPENAI_API_KEY_VAL,
    "base_url": AZURE_OPENAI_ENDPOINT_VAL,
    "api_type": "azure",
    "api_version": AZURE_OPENAI_API_VERSION_VAL,
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
REFORMULATOR_NAME = "QueryReformulator"

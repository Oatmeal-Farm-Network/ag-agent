

# 🌾 AI-Powered Agricultural Advisor (`ag-agent`)

This project is an advanced conversational AI chatbot designed to provide expert guidance on a wide range of agricultural topics. It leverages a multi-agent system powered by Microsoft AutoGen and large language models from Azure OpenAI to simulate a consultation with a team of AI experts.

## ✨ Key Features

  * **Conversational AI:** Ask complex farming questions in natural language, from pest control and crop diseases to weather suitability.
  * **Multi-Agent System:** Utilizes a team of specialized AI agents (e.g., Expert Advisor, User Proxy) that collaborate to find the best answer.
  * **Real-time Data:** Integrates with external APIs (like Open-Meteo) to provide advice based on current weather conditions.
  * **Cloud Integration:** Powered by Azure OpenAI for cutting-edge language understanding and Azure Cosmos DB for data persistence.
  * **Interactive UI:** A user-friendly, chat-based web interface built with Streamlit.
  * **Containerized & Deployable:** Fully containerized with Docker for easy, consistent, and reliable deployment on any machine.

## 🛠️ Tech Stack

  * **Backend:** Python
  * **AI Framework:** Microsoft AutoGen
  * **Web UI:** Streamlit
  * **LLM Provider:** Azure OpenAI
  * **Database:** Azure Cosmos DB
  * **Containerization:** Docker

## 🚀 Getting Started

Follow these instructions to get a local copy of the project up and running for development or deployment.

### Prerequisites

You must have the following software installed on your machine:

  * [Git](https://git-scm.com/downloads)
  * [Docker Desktop](https://www.docker.com/products/docker-desktop/)

### Setup & Installation

1.  **Clone the Repository**
    Open your terminal and clone the `ag-agent` repository:

    ```bash
    git clone https://github.com/bringesh2001/ag-agent.git
    cd ag-agent
    ```

2.  **Create the Environment File**
    Create a file named `.env` in the root of the project folder. Copy the contents of `.env.example` (or the block below) into your new `.env` file and fill in your actual credentials.

    ```env
    # .env file content

    # --- Azure OpenAI Credentials ---
    AZURE_OPENAI_API_BASE=https://your-endpoint-name.openai.azure.com/
    AZURE_OPENAI_API_KEY=YOUR_AZURE_OPENAI_API_KEY_HERE
    AZURE_OPENAI_API_VERSION=2023-07-01-preview
    AZURE_OPENAI_CHAT_DEPLOYMENT_NAME=YOUR_CHAT_MODEL_DEPLOYMENT_NAME_HERE
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT=YOUR_EMBEDDING_MODEL_DEPLOYMENT_NAME_HERE

    # --- Azure Cosmos DB Credentials ---
    COSMOS_ENDPOINT=https://your-cosmosdb-name.documents.azure.com:443/
    COSMOS_KEY=YOUR_COSMOS_DB_PRIMARY_KEY_HERE
    ```

### Running the Application with Docker

With Docker Desktop running, use these two commands from the root project directory (`/ag-agent`).

1.  **Build the Docker Image**
    This command packages the application and all its dependencies into a container image. This may take a few minutes the first time.

    ```bash
    docker build -t ag-agent .
    ```

2.  **Run the Docker Container**
    This command starts the application. The `-p 8000:8000` flag makes the app accessible on your local machine, and `--env-file .env` securely injects your secrets.

    ```bash
    docker run -p 8000:8000 --env-file .env ag-agent
    ```

3.  **Access the Application**
    Open your web browser and navigate to:
    [http://localhost:8000](https://www.google.com/search?q=http://localhost:8000)

## 📖 Usage

Once the application is running in your browser, simply type your farm-related question into the chat input box at the bottom of the screen and press Enter. The AI agents will begin their consultation, and you can view their "thinking process" in the expandable status box. The final, summarized advice will appear in the main chat window.

## 📁 Project Structure

A brief overview of the key directories and files:

```
/ag-agent
├── autogen_module/     # Contains the definitions for the AutoGen agents
├── external_apis/      # Code for connecting to external services (e.g., weather)
├── ui_module/          # Streamlit UI components and helper functions
├── .env.example        # Template for environment variables
├── app.py              # The main Streamlit application entry point
├── config.py           # Handles configuration and loading environment variables
├── Dockerfile          # Recipe for building the Docker container image
└── requirements.txt    # List of Python dependencies
```



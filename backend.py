# Alternative backend.py approach - Using GroupChat message hooks

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import re
import autogen
import asyncio
import json


# --- Local Project Imports ---
from config import (
    autogen_llm_config_list, EXPERT_ADVISOR_NAME, USER_PROXY_NAME,
    SEARCHER_NAME, PROCESSOR_NAME, SOIL_NAME, NUTRITION_NAME,
    WEATHER_NAME, LIVESTOCK_BREED_NAME
)
from autogen_module.agents import all_agents

from starlette.websockets import WebSocketState # makes WebSocket connection more readable and robust.

from fastapi.middleware.cors import CORSMiddleware

# --- FastAPI App Setup ---
app = FastAPI()
# --- CORS MIDDLEWARE SETUP ---
# List of origins that are allowed to make requests to this API
# For development, you can allow localhost. For production, you should
# list your actual frontend domain, e.g., ["https://your-domain.com"]
# Updated CORS configuration for Azure Container Apps
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:3001",
    # Add your Azure Container Apps URL
    "https://multi-container-agent-app.orangepond-1d33f6fb.eastus.azurecontainerapps.io",
    # Also add the WebSocket protocol variants
    "wss://multi-container-agent-app.orangepond-1d33f6fb.eastus.azurecontainerapps.io",
    # Add wildcard for any subdomain if needed
    "https://*.azurecontainerapps.io"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

# Add this additional middleware for WebSocket support
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=[
        "localhost", 
        "127.0.0.1", 
        "multi-container-agent-app.orangepond-1d33f6fb.eastus.azurecontainerapps.io",
        "*.azurecontainerapps.io"
    ]
)
# --- END OF CORS SETUP ---

# --- Helper Functions ---
def extract_final_advice(autogen_messages):
    if not autogen_messages: return None
    for msg in reversed(autogen_messages):
        if msg.get("name") == EXPERT_ADVISOR_NAME:
            content = msg.get("content", "").strip()
            if content: return re.sub(r'\s*TERMINATE\s*$', '', content, flags=re.IGNORECASE).strip()
    return None

# REPLACING  the old selection function(custom speaker selection) with this one:

def robust_speaker_selection(last_speaker: autogen.Agent, groupchat: autogen.GroupChat) -> autogen.Agent:
    """
    A more resilient method to select the next speaker and prevent stalls.
    """
    messages = groupchat.messages
    
    # If the last message is from the user, start the workflow.
    if last_speaker.name == USER_PROXY_NAME:
        return groupchat.agent_by_name(SEARCHER_NAME)
        
    # If the last message contains "TERMINATE", the conversation is over.
    last_message_content = messages[-1].get("content", "").upper()
    if "TERMINATE" in last_message_content:
        return groupchat.agent_by_name(USER_PROXY_NAME)

    # Pre-defined linear workflow
    workflow = {
        SEARCHER_NAME: PROCESSOR_NAME,
        PROCESSOR_NAME: SOIL_NAME,
        SOIL_NAME: NUTRITION_NAME,
        NUTRITION_NAME: EXPERT_ADVISOR_NAME,
        WEATHER_NAME: EXPERT_ADVISOR_NAME,
        LIVESTOCK_BREED_NAME: EXPERT_ADVISOR_NAME
    }

    # If the last speaker is in our defined workflow, get the next one.
    if next_speaker_name := workflow.get(last_speaker.name):
        return groupchat.agent_by_name(next_speaker_name)
    
    # --- FALLBACK LOGIC ---
    # If the speaker is not in the workflow (e.g., ContextProcessor),
    # or at an unexpected step, route to the Lead Advisor to conclude.
    if last_speaker.name != EXPERT_ADVISOR_NAME:
        print(f"--- [WARN] Unexpected speaker '{last_speaker.name}'. Defaulting to LeadAgriculturalAdvisor. ---")
        return groupchat.agent_by_name(EXPERT_ADVISOR_NAME)

    # If the Lead Advisor just spoke, end the conversation.
    return groupchat.agent_by_name(USER_PROXY_NAME)

# Custom GroupChatManager that streams messages
class StreamingGroupChatManager(autogen.GroupChatManager):
    def __init__(self, groupchat, websocket, **kwargs):
        super().__init__(groupchat, **kwargs)
        self.websocket = websocket

    async def a_run_chat(self, messages, sender, config=None):
        """
        Overrides the main chat loop to send UI notifications.
        This method is called by `a_initiate_chat`.
        """
        # The conversation starts with the sender (User Proxy)
        # We can optionally send this to the UI
        # await self._send_step_to_ui(sender.name)

        for i in range(self.groupchat.max_round):
            self.groupchat.messages = messages
            
            # 1. Select the next speaker
            speaker = self.groupchat.select_speaker(sender, self.groupchat)
            
            # 2. <<< KEY CHANGE >>>
            #    Send the "agent is working" step to the UI *before* the agent runs.
            await self._send_step_to_ui(speaker.name)

            # 3. Let the speaker generate a reply
            reply = await speaker.a_generate_reply(messages, sender=self.groupchat, config=config)

            if reply is None:
                break # Chat finished
                
            # 4. Broadcast the reply to all other agents
            self.a_broadcast(reply, sender=speaker)
            messages.append(reply)
            
            # 5. Check for termination
            if "TERMINATE" in str(reply.get("content", "")):
                break
        
        return True, None

    async def _send_step_to_ui(self, agent_name: str):
        """Helper to send the 'agent_step' message to the frontend."""
        try:
            # This is the EXACT message format the frontend expects
            step_data = {
                "type": "agent_step",
                "agent_name": agent_name
            }
            print(f"--> Sending agent_step for: {agent_name}")
            if self.websocket.client_state == WebSocketState.CONNECTED:
                await self.websocket.send_text(json.dumps(step_data))
                await asyncio.sleep(0.1) # Small delay for the UI to update
        except Exception as e:
            print(f"--- Error sending agent step: {e} ---")

# In backend.py, add this entire class definition before your websocket_endpoint function.

class StreamingGroupChat(autogen.GroupChat):
    """A custom GroupChat that streams agent steps over a WebSocket."""
    def __init__(self, websocket: WebSocket, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.websocket = websocket
        self.loop = asyncio.get_running_loop()
        # Add a list to track our streaming tasks to prevent race conditions
        self.streaming_tasks = []

    def append(self, message: dict, speaker: autogen.Agent):
        # This synchronous method is called by AutoGen's internal loop
        super().append(message, speaker)
        if speaker.name != USER_PROXY_NAME:
            # Use run_coroutine_threadsafe to safely schedule the async websocket
            # send from this synchronous method onto the main event loop.
            task = asyncio.run_coroutine_threadsafe(
                self._stream_message_to_ui(speaker), self.loop
            )
            self.streaming_tasks.append(task)

    async def _stream_message_to_ui(self, speaker: autogen.Agent):
        """Sends an 'agent_step' message to the frontend."""
        try:
            # Check the WebSocket state correctly before sending
            if self.websocket.client_state == WebSocketState.CONNECTED:
                step_data = {"type": "agent_step", "agent_name": speaker.name}
                await self.websocket.send_text(json.dumps(step_data))
                await asyncio.sleep(0.1) # Small sleep to prevent UI flooding
        except Exception as e:
            print(f"❌ CRITICAL ERROR in _stream_message_to_ui: {e.__class__.__name__}: {e}")

# --- WebSocket Chat Logic ---

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    user_proxy = next((agent for agent in all_agents if agent.name == USER_PROXY_NAME), None)
    if not user_proxy:
        await websocket.send_text(json.dumps({"type": "error", "content": "UserProxyAgent not found."}))
        await websocket.close()
        return

    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            
            # --- Start of logic for a single user message ---
            try:
                # We define a temporary async function to wrap the chat logic.
                # This allows us to apply a timeout to the entire process.
                async def chat_task():
                    # Get user query from the payload
                    text_query = payload.get("text", "")
                    images = payload.get("images", [])
                    user_id = payload.get("user_id", "default_user")
                    
                    print(f"🚀 Processing query: '{text_query}' with {len(images)} images.")

                    # Process images if they exist
                    image_analysis, image_ids = "", []
                    if images:
                        image_analysis, image_ids = await process_images_with_gpt4o(images, text_query, user_id)
                    
                    enhanced_message = create_enhanced_message(text_query, image_analysis, user_id, image_ids)

                    # Set up the chat using our streaming class and robust selection
                    groupchat = StreamingGroupChat(
                        websocket=websocket, agents=all_agents, messages=[], max_round=15, 
                        speaker_selection_method=robust_speaker_selection # <-- Use robust function
                    )
                    manager = autogen.GroupChatManager(
                        groupchat=groupchat, llm_config={"config_list": autogen_llm_config_list}
                    )
                    
                    # Run the main agent conversation
                    await user_proxy.a_initiate_chat(manager, message=enhanced_message)
                    
                    # Wait for any final streaming messages to finish to prevent a race condition

                    # Clear any pending streaming tasks before final answer
                    try:
                        # Cancel any pending streaming tasks
                        for task in groupchat.streaming_tasks:
                            if not task.done():
                                task.cancel()
                        
                        # Send a clear signal to stop any UI loading states
                        clear_signal = {"type": "clear_agent_status"}
                        if websocket.client_state == WebSocketState.CONNECTED:
                            await websocket.send_text(json.dumps(clear_signal))
                            await asyncio.sleep(0.1)  # Brief pause for UI to process
                            
                    except Exception as e:
                        print(f"--- [WARN] Error clearing streaming tasks: {e} ---")
                    
                 

                    
                    # Extract and send the final answer
                    final_advice = extract_final_advice(groupchat.messages)
                    final_data = {"type": "final_answer", "content": final_advice or "The consultation has concluded."}
                    if websocket.client_state == WebSocketState.CONNECTED:
                        await websocket.send_text(json.dumps(final_data))

                # Now, run the entire chat task with a 60-second timeout
                await asyncio.wait_for(chat_task(), timeout=60.0)

            except asyncio.TimeoutError:
                print("❌ --- AutoGen chat TIMED OUT! --- ❌")
                error_data = {"type": "error", "content": "The consultation is taking too long. Please try rephrasing your question."}
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_text(json.dumps(error_data))
            except Exception as e:
                # This catches errors from within the chat_task (e.g., agent errors)
                error_msg = f"An error occurred during the agent workflow: {e}"
                print(f"❌ {error_msg}")
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_text(json.dumps({"type": "error", "content": str(e)}))
                    completion_signal = {"type": "conversation_complete"}
                    await websocket.send_text(json.dumps(completion_signal))
            # --- End of logic for a single user message ---

    except WebSocketDisconnect:
        print("Client disconnected.")
    except Exception as e:
        # This catches errors in the websocket connection itself
        print(f"An error occurred in the WebSocket endpoint: {e}")


# --- NEW: Process images with GPT-4o ---
async def process_images_with_gpt4o(images: list, text_query: str, user_id: str):
    """Process images with GPT-4o and store in Cosmos DB"""
    
    # Import here to avoid circular imports
    from database_module.cosmos_retriever import add_image_to_cosmos, add_multimodal_memory_to_cosmos
    
    image_analysis_parts = []
    image_ids = []
    
    for img in images:
        try:
            print(f"--- Processing image: {img['name']} ---")
            
            # Analyze image with GPT-4o (async call)
            analysis = await analyze_single_image_with_gpt4o(img['data'], text_query)
            print(f"--- GPT-4o analysis: {analysis[:100]}... ---")
            
            image_analysis_parts.append(analysis)
            
            # Store image in Cosmos DB
            image_id = add_image_to_cosmos(
                image_data=img['data'],
                image_description=analysis,
                user_id=user_id,
                metadata={
                    "file_name": img['name'],
                    "file_size": len(img['data']),
                    "original_query": text_query
                }
            )
            
            if image_id:
                image_ids.append(image_id)
                print(f"--- Image stored with ID: {image_id} ---")
                
        except Exception as e:
            print(f"Error processing image {img['name']}: {e}")
            error_msg = f"Error analyzing image {img['name']}: {str(e)}"
            image_analysis_parts.append(error_msg)
    
    return "\n\n".join(image_analysis_parts), image_ids

# --- NEW: Analyze single image with GPT-4o ---
async def analyze_single_image_with_gpt4o(image_data: str, text_query: str):
    """Analyze a single image with GPT-4o vision"""
    
    # Import Azure OpenAI client and asyncio
    from config import embedding_client
    import asyncio
    
    # Prepare content for GPT-4o
    content = [
        {
            "type": "text",
            "text": f"Look at this agricultural image and provide a brief, clear description in 1-2 sentences. Focus on:\n- What plant/crop you see\n- Any obvious problems or symptoms\n\nUser question: {text_query}\n\nKeep it simple and direct - this will be used for agricultural consultation."
        },
        {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{image_data}"
            }
        }
    ]
    
    try:
        # Run the sync Azure OpenAI call in a thread to avoid blocking
        def call_gpt4o():
            return embedding_client.chat.completions.create(
                model="gpt-4o",
                messages=[{
                    "role": "user",
                    "content": content
                }],
                max_tokens=500
            )
        
        # Execute the sync call in a thread
        response = await asyncio.to_thread(call_gpt4o)
        
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"Error calling GPT-4o: {e}")
        return f"Unable to analyze image: {str(e)}"

# --- NEW: Create enhanced message for AutoGen ---
def create_enhanced_message(text_query: str, image_analysis: str, user_id: str, image_ids: list):
    """Create enhanced message for AutoGen agents"""
    
    # Count images for context
    image_count = len(image_ids) if image_ids else 0
    
    enhanced_message = f"""
USER_ID: {user_id}
QUERY_TEXT: {text_query}

IMAGE_CONTEXT:
- Number of images analyzed: {image_count}
- Images contain: {image_analysis}

IMAGE_IDS: {image_ids}

RESPONSE STRUCTURE:
Please provide your response in this exact format:

📸 What I See in Your Images:
[Brief summary of what you observe in each image - 2-3 sentences max]

🔍 My Analysis:
[What the symptoms indicate - 2-3 sentences max]

🌾 My Recommendations:
[3-5 specific, actionable steps in simple language]

Keep your response conversational, practical, and easy to understand. Focus on immediate actions the farmer can take.
"""
    
    return enhanced_message.strip()

# Run the Server
import os

if __name__ == "__main__":
    # Use environment variables for Azure deployment
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 8000))
    
    uvicorn.run("backend:app", host=host, port=port, reload=False)
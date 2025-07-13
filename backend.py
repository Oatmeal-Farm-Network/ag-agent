# =============================================================================
# IMPORTS
# =============================================================================
import os
import re
import json
import asyncio
import base64
from datetime import datetime, timezone
import uuid

import uvicorn
import autogen
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocketState
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

# --- Local project imports for the LangChain architecture ---
from config import (
    autogen_llm_config_list, USER_PROXY_NAME, EXPERT_ADVISOR_NAME,
    SEARCHER_NAME, PROCESSOR_NAME, SOIL_NAME, NUTRITION_NAME,
    WEATHER_NAME, LIVESTOCK_BREED_NAME,REFORMULATOR_NAME
)
from autogen_module.agents import all_agents
from memory_module.langchain_setup import get_session_history, vector_store
from utilities_module.vision_utils import process_image # Assuming this now just returns a description
from utilities_module.audio_utils import process_audio # Assuming this now just returns a transcription

# =============================================================================
# FASTAPI APP SETUP
# =============================================================================
app = FastAPI(title="Agricultural Advisor API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# HELPER FUNCTIONS & CUSTOM AUTOGEN CLASSES
# =============================================================================
def extract_final_advice(autogen_messages):
    """Extract the final advice from AutoGen conversation messages."""
    if not autogen_messages: return None
    for msg in reversed(autogen_messages):
        if msg.get("name") == EXPERT_ADVISOR_NAME:
            content = msg.get("content", "").strip()
            if content:
                return re.sub(r'\s*TERMINATE\s*$', '', content, flags=re.IGNORECASE).strip()
    return None


def robust_speaker_selection(last_speaker: autogen.Agent, groupchat: autogen.GroupChat):
    """A resilient method to select the next speaker."""
    messages = groupchat.messages
    last_message_content = messages[-1].get("content", "")

    # Workflow: User -> QueryReformulator -> SemanticSearcher -> Others
    if last_speaker.name == USER_PROXY_NAME:
        return groupchat.agent_by_name(REFORMULATOR_NAME)
        
    if last_speaker.name == REFORMULATOR_NAME:
        # <<< FIX for the loop >>>
        # If the reformulator asks a question, go back to the user.
        if last_message_content.endswith("?"):
            return groupchat.agent_by_name(USER_PROXY_NAME)
        # Otherwise, continue to the searcher.
        return groupchat.agent_by_name(SEARCHER_NAME)

    if "TERMINATE" in last_message_content.upper():
        return groupchat.agent_by_name(USER_PROXY_NAME)
    
    # Check for explicit 'NEXT_SPEAKER' cue from other agents
    match = re.search(r"NEXT_SPEAKER:\s*(\w+)", last_message_content)
    if match:
        next_speaker_name = match.group(1)
        if next_speaker_agent := groupchat.agent_by_name(next_speaker_name):
            return next_speaker_agent

    # Fallback to the rest of the workflow
    workflow = {
        SEARCHER_NAME: PROCESSOR_NAME, PROCESSOR_NAME: SOIL_NAME, SOIL_NAME: NUTRITION_NAME,
        NUTRITION_NAME: EXPERT_ADVISOR_NAME, WEATHER_NAME: EXPERT_ADVISOR_NAME,
        LIVESTOCK_BREED_NAME: EXPERT_ADVISOR_NAME
    }
    if next_speaker_name := workflow.get(last_speaker.name):
        return groupchat.agent_by_name(next_speaker_name)
    
    if last_speaker.name != EXPERT_ADVISOR_NAME:
        return groupchat.agent_by_name(EXPERT_ADVISOR_NAME)
        
    return groupchat.agent_by_name(USER_PROXY_NAME)
class StreamingGroupChat(autogen.GroupChat):
    """Custom GroupChat that streams agent steps and handles conversation completion."""
    def __init__(self, agents, messages, max_round=15, speaker_selection_method="auto", websocket: WebSocket = None):
        super().__init__(agents, messages, max_round, speaker_selection_method)
        self.websocket = websocket
        self.conversation_complete = False

    def append(self, message: dict, speaker: autogen.Agent):
        super().append(message, speaker)
        if self.conversation_complete: return
        if self.websocket and speaker.name != USER_PROXY_NAME:
            try:
                step_data = {"type": "agent_step", "agent_name": speaker.name}
                asyncio.create_task(self.websocket.send_text(json.dumps(step_data)))
            except Exception as e:
                print(f"Could not stream message to UI: {e}")


# NEW HELPER FUNCTION TO CONVERT CHAT HISTORY
def convert_lc_to_autogen_history(lc_messages: list[BaseMessage]) -> list[dict]:
    """Converts LangChain message history to AutoGen's expected format."""
    autogen_history = []
    for msg in lc_messages:
        if isinstance(msg, HumanMessage):
            autogen_history.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage):
            # Find which agent sent this message if possible, otherwise default to advisor
            # This part is complex as history doesn't store agent names well.
            # We'll approximate by having the user proxy speak the user messages
            # and the expert advisor speak the AI messages.
            autogen_history.append({"role": "assistant", "name": EXPERT_ADVISOR_NAME, "content": msg.content})
    return autogen_history
# =============================================================================
# MAIN WEBSOCKET LOGIC (REFACTORED WITH LANGCHAIN)
# =============================================================================
async def handle_chat_message(websocket: WebSocket, payload: dict):
    """Handles all incoming user messages using the new LangChain architecture."""
    user_proxy = next((agent for agent in all_agents if agent.name == USER_PROXY_NAME), None)
    if not user_proxy:
        await websocket.send_text(json.dumps({"type": "error", "content": "Critical Error: UserProxyAgent not found."}))
        return

    try:
        # --- 1. Get Session & Short-Term History ---
        user_id = payload.get("user_id", "default_user")
        session_id = payload.get("session_id")
        text_query = payload.get("text", "")
        images_b64 = payload.get("images", [])

        if not session_id:
            session_id = str(uuid.uuid4())
            await websocket.send_text(json.dumps({"type": "session_created", "session_id": session_id}))

        # Get the short-term memory handler for this session from LangChain
        history = get_session_history(session_id, user_id)
        previous_autogen_messages = convert_lc_to_autogen_history(history.messages)
        history.add_user_message(text_query)

        # --- 2. Process Media & Add to Long-Term Memory ---
        media_descriptions = []
        for img_data in images_b64:
            image_bytes = base64.b64decode(img_data['data'])
            # Assuming process_image now just returns a description
            _, description = await asyncio.to_thread(process_image, image_bytes, user_id, session_id)
            if description:
                media_descriptions.append(f"Image Analysis: {description}")
        
        # Add all text content to the long-term vector store
        content_to_vectorize = [text_query] + media_descriptions
        vector_store.add_texts(
            texts=content_to_vectorize,
            metadatas=[{"user_id": user_id, "session_id": session_id, "timestamp": datetime.now(timezone.utc).isoformat()}] * len(content_to_vectorize)
        )
        
        # --- 3. Run Agentic Workflow ---
        # The enhanced message now includes context from the media analysis
       # --- FIX: CREATE A STRUCTURED JSON MESSAGE ---
        initial_context = "\n".join(media_descriptions)
        initial_message_dict = {
            "query_text": text_query,
            "user_id": user_id,
            "media_context": initial_context
        }
        initial_message_json = json.dumps(initial_message_dict)
        
        # --- FIX: PASS THE LOADED HISTORY TO THE GROUPCHAT ---
        groupchat = StreamingGroupChat(
            agents=all_agents,
            messages=previous_autogen_messages, # Pass loaded history
            max_round=15,
            speaker_selection_method=robust_speaker_selection,
            websocket=websocket
        )
        manager = autogen.GroupChatManager(groupchat=groupchat, llm_config={"config_list": autogen_llm_config_list})
        
        # The user proxy initiates the chat with the structured JSON message
        await user_proxy.a_initiate_chat(manager, message=initial_message_json)
        
        # --- 4. Finalize, Log, and Respond ---
        groupchat.conversation_complete = True
        
        final_advice = extract_final_advice(groupchat.messages)
        final_advice_text = final_advice or "The consultation has concluded."
        
        # Log the AI's final response to the short-term history
        history.add_ai_message(final_advice_text)
        
        await websocket.send_text(json.dumps({"type": "final_answer", "content": final_advice_text}))

    except Exception as e:
        error_message = f"An error occurred in the chat handler: {e}"
        print(error_message)
        await websocket.send_text(json.dumps({"type": "error", "content": error_message}))

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            await handle_chat_message(websocket, payload)
    except WebSocketDisconnect:
        print("Client disconnected.")
    except Exception as e:
        print(f"An error occurred in the WebSocket endpoint: {e}")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("backend:app", host="0.0.0.0", port=8000, reload=True)
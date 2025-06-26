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

# --- FastAPI App Setup ---
app = FastAPI()

# --- Helper Functions ---
def extract_final_advice(autogen_messages):
    if not autogen_messages: return None
    for msg in reversed(autogen_messages):
        if msg.get("name") == EXPERT_ADVISOR_NAME:
            content = msg.get("content", "").strip()
            if content: return re.sub(r'\s*TERMINATE\s*$', '', content, flags=re.IGNORECASE).strip()
    return None

def custom_speaker_selection(last_speaker, groupchat):
    last_message = groupchat.messages[-1]
    if last_message.get("tool_calls"): return last_speaker
    last_content = last_message.get('content', '')
    if match := re.search(r"NEXT_SPEAKER:\s*(\w+)", last_content, re.IGNORECASE):
        if next_speaker := groupchat.agent_by_name(match.group(1).strip()): return next_speaker
    workflow = {
        USER_PROXY_NAME: SEARCHER_NAME, SEARCHER_NAME: PROCESSOR_NAME,
        PROCESSOR_NAME: SOIL_NAME, SOIL_NAME: NUTRITION_NAME,
        NUTRITION_NAME: EXPERT_ADVISOR_NAME, WEATHER_NAME: EXPERT_ADVISOR_NAME,
        LIVESTOCK_BREED_NAME: EXPERT_ADVISOR_NAME
    }
    if next_speaker_name := workflow.get(last_speaker.name):
        return groupchat.agent_by_name(next_speaker_name)
    return None

# Custom GroupChatManager that streams messages
class StreamingGroupChatManager(autogen.GroupChatManager):
    def __init__(self, groupchat, websocket, **kwargs):
        super().__init__(groupchat, **kwargs)
        self.websocket = websocket
        
    async def a_send(self, message, recipient, request_reply=None, silent=False):
        # Send the message as usual
        result = await super().a_send(message, recipient, request_reply, silent)
        
        # Stream the message to the UI if it's from an agent (not user proxy)
        if hasattr(recipient, 'name') and recipient.name != USER_PROXY_NAME:
            await self.stream_message_to_ui(message, recipient)
            
        return result
        
    async def stream_message_to_ui(self, message, recipient):
        try:
            content = message.get("content", "") if isinstance(message, dict) else str(message)
            
            # Clean up the content
            cleaned_content = re.sub(r'\s*TERMINATE\s*$', '', content, flags=re.IGNORECASE).strip()
            cleaned_content = re.sub(r'NEXT_SPEAKER:\s*\w+', '', cleaned_content, flags=re.IGNORECASE).strip()
            
            if cleaned_content and hasattr(recipient, 'name'):
                step_data = {
                    "type": "agent_message",
                    "agent_name": recipient.name,
                    "content": cleaned_content,
                    "timestamp": asyncio.get_event_loop().time()
                }
                
                print(f"--- Streaming to UI: {recipient.name} ---")
                print(f"--- Content: {cleaned_content[:100]}... ---")
                
                if self.websocket.client_state == 1:  # WebSocket.OPEN
                    await self.websocket.send_text(json.dumps(step_data))
                    await asyncio.sleep(0.1)
                    
        except Exception as e:
            print(f"--- Error streaming message: {e} ---")

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
            initial_query = await websocket.receive_text()
            print(f"--- Received query: {initial_query} ---")

            # Set up GroupChat with custom streaming manager
            groupchat = autogen.GroupChat(
                agents=all_agents, 
                messages=[], 
                max_round=20, 
                speaker_selection_method=custom_speaker_selection
            )
            
            # Use our custom streaming manager
            manager = StreamingGroupChatManager(
                groupchat=groupchat, 
                websocket=websocket,
                llm_config={"config_list": autogen_llm_config_list}
            )
            
            print("--- Starting chat ---")
            await user_proxy.a_initiate_chat(manager, message=initial_query)
            print("--- Chat completed ---")

            # Send the final answer
            final_advice = extract_final_advice(groupchat.messages)
            final_data = {
                "type": "final_answer",
                "content": final_advice or "The consultation concluded, but a final recommendation was not formulated."
            }
            await websocket.send_text(json.dumps(final_data))

    except WebSocketDisconnect:
        print("Client disconnected.")
    except Exception as e:
        print(f"An error occurred in WebSocket: {e}")
        import traceback
        traceback.print_exc()
        error_data = {"type": "error", "content": f"An error occurred: {str(e)}"}
        if websocket.client_state == 1:
             await websocket.send_text(json.dumps(error_data))
    finally:
        print("WebSocket connection logic finished.")

# Run the Server
if __name__ == "__main__":
    uvicorn.run("backend:app", host="127.0.0.1", port=8000, reload=True)
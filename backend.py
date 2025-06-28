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
            # Receive JSON payload instead of just text
            data = await websocket.receive_text()
            payload = json.loads(data)
            
            # Extract data from payload
            text_query = payload.get("text", "")
            images = payload.get("images", [])
            user_id = payload.get("user_id", "default_user")
            
            print(f"--- Received multimodal query: {text_query} with {len(images)} images ---")

            # Process images if present
            image_analysis = ""
            image_ids = []
            if images:
                image_analysis, image_ids = await process_images_with_gpt4o(images, text_query, user_id)
                print(f"--- Image analysis completed: {len(image_ids)} images processed ---")

            # Create enhanced message for AutoGen
            enhanced_message = create_enhanced_message(text_query, image_analysis, user_id, image_ids)

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
            
            print("--- Starting chat with enhanced message ---")
            await user_proxy.a_initiate_chat(manager, message=enhanced_message)
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
if __name__ == "__main__":
    uvicorn.run("backend:app", host="127.0.0.1", port=8000, reload=True)
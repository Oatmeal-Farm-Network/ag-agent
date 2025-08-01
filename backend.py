# =============================================================================
# AGENT-BASED AGRICULTURAL ADVISOR BACKEND
# =============================================================================
# A FastAPI backend that provides agricultural advice using multi-agent AI
# with voice conversation capabilities and Azure services integration.
# =============================================================================

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library imports
import asyncio
import base64
import json
import os
import re
import tempfile
import time
from datetime import datetime

# Third-party imports
from dotenv import load_dotenv
from fastapi import Body, FastAPI, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from openai import AzureOpenAI
from pydantic import BaseModel
from pydub import AudioSegment
from starlette.websockets import WebSocketState
from tiktoken import encoding_for_model
import azure.cognitiveservices.speech as speechsdk
import uvicorn

# Local application imports
from autogen_module.routeagents import AgentRouter
from config import IMAGE_BLOB_CONTAINER_NAME, blob_service_client, memory_client  # needed clients
from utilities_module.blob_utils import upload_to_blob_storage
from utilities_module.session_storage import SessionStorageManager

load_dotenv()

# Create a client just for this vision task
vision_client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_API_BASE")
)

# =============================================================================
# CONFIGURATION
# =============================================================================

# Azure Speech Configuration
AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION")

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_API_BASE")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")


azure_openai_client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    api_version=AZURE_OPENAI_API_VERSION,
    azure_endpoint=AZURE_OPENAI_ENDPOINT
)




# CORS Configuration
ORIGINS = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:3001",
    "https://multi-container-agent-app.orangepond-1d33f6fb.eastus.azurecontainerapps.io",
    "wss://multi-container-agent-app.orangepond-1d33f6fb.eastus.azurecontainerapps.io",
    "https://*.azurecontainerapps.io"
]

ALLOWED_HOSTS = [
    "localhost", 
    "127.0.0.1", 
    "multi-container-agent-app.orangepond-1d33f6fb.eastus.azurecontainerapps.io",
    "*.azurecontainerapps.io"
]


#helps FastAPI validate that incoming requests to your new endpoint have the correct format (i.e., a JSON object with a "text" field).
class TextToSpeechRequest(BaseModel):
    text: str
# =============================================================================
# FASTAPI APP SETUP
# =============================================================================

app = FastAPI(title="Agricultural Advisor API", version="1.0.0")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

# Trusted Host Middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=ALLOWED_HOSTS
)

# =============================================================================
# WEBSocket ENDPOINT
# =============================================================================

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for chat and voice conversations."""
    await websocket.accept()
    
    session_storage = SessionStorageManager(max_messages_per_chunk=100)

    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)

            # =================================================================
            # PAGINATED HISTORY LOADING
            # =================================================================
            if payload.get("type") == "load_history":
                session_id = payload.get("sessionId")
                offset = int(payload.get("offset", 0))
                limit = int(payload.get("limit", 20))
                messages = session_storage.get_messages_paginated(session_id, offset, limit)
                await websocket.send_text(json.dumps({
                    "type": "history",
                    "messages": messages,
                    "offset": offset,
                    "limit": limit
                }))
                continue

            # =================================================================
            # VOICE CONVERSATION HANDLING
            # =================================================================
            if payload.get("type") == "voice_conversation":
                await handle_voice_conversation(websocket, payload)
                continue

            # =================================================================
            # AUDIO MESSAGE HANDLING (for main chat)
            # =================================================================
            if payload.get("type") == "audio":
                await handle_audio_message(websocket, payload)
                continue

            # =================================================================
            # TEXT/IMAGE MESSAGE HANDLING
            # =================================================================
            await handle_text_image_message(websocket, payload)

    except WebSocketDisconnect:
        print("Client disconnected.")
    except Exception as e:
        print(f"An error occurred in the WebSocket endpoint: {e}")


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def clean_for_tts(text):
    """Clean text for better TTS output by removing markdown and formatting."""
    # Remove markdown headers
    text = re.sub(r'^\s*#{1,6}\s*.*$', '', text, flags=re.MULTILINE)
    
    # Remove hashtags
    text = re.sub(r'#\w+', '', text)
    text = re.sub(r'\bhashtag\b', '', text, flags=re.IGNORECASE)
    
    # Remove markdown formatting
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    
    # Remove links and URLs
    text = re.sub(r'\[.*?\]\(.*?\)', '', text)
    text = re.sub(r'http\S+', '', text)
    
    # Remove numbered list prefixes
    text = re.sub(r'^\s*\d+\.\s*', '', text, flags=re.MULTILINE)
    
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def synthesize_speech_from_text(text):
    """Synthesize text to speech and return audio bytes (WAV format) in memory, using the same approach as charlie_voice_demo.py."""
    try:
        speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_SPEECH_REGION)
        speech_config.speech_synthesis_voice_name = "en-US-JennyNeural"
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
        result = synthesizer.speak_text_async(text).get()
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            return result.audio_data
        else:
            print(f"❌ Speech synthesis failed: {result.reason}")
            return None
    except Exception as e:
        print(f"❌ Error in speech synthesis: {e}")
        return None



def text_to_speech_base64(text):
    """Convert text to speech and return as base64 string (in-memory only)."""
    try:
        audio_bytes = synthesize_speech_from_text(text)  # Use the same function for consistency
        if audio_bytes:
            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
            return audio_b64
        else:
            return None
    except Exception as e:
        print(f"❌ Error converting text to speech: {e}")
        return None

# =============================================================================
# IMAGE PROCESSING FUNCTIONS
# =============================================================================

async def analyze_single_image_with_gpt4o(image_data: str, text_query: str):
    """Analyze a single image with GPT-4o vision."""
    
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
        def call_gpt4o():
            # Use the new, locally defined client and your chat deployment
            return azure_openai_client.chat.completions.create(
                model=AZURE_OPENAI_DEPLOYMENT,
                messages=[{"role": "user", "content": content}],
                max_tokens=500
            )
        
        response = await asyncio.to_thread(call_gpt4o)
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"Error calling GPT-4o: {e}")
        return f"Unable to analyze image: {str(e)}"

async def process_images_with_gpt4o(images: list, text_query: str, user_id: str):
    """Process images with GPT-4o and prepare metadata for memory."""

    image_analysis_parts = []
    image_ids = []
    attachments = []
    
    for img in images:
        try:
            print(f"--- Processing image: {img['name']} ---")
            
            # Analyze image with GPT-4o
            analysis = await analyze_single_image_with_gpt4o(img['data'], text_query)
            print(f"--- GPT-4o analysis: {analysis[:100]}... ---")
            
            image_analysis_parts.append(analysis)
            
            # Store image in Blob Storage to get a URL
            image_bytes = base64.b64decode(img['data'])

            blob_url, image_id = upload_to_blob_storage(blob_service_client, IMAGE_BLOB_CONTAINER_NAME, image_bytes, "jpg")

            # Prepare attachment metadata for mem0
            attachment = {
                "id": image_id,
                "url": blob_url,
                "description": analysis
            }
            attachments.append(attachment)
            image_ids.append(image_id)
            print(f"--- Image stored in Blob Storage with ID: {image_id} ---")
                
        except Exception as e:
            print(f"Error processing image {img['name']}: {e}")
            error_msg = f"Error analyzing image {img['name']}: {str(e)}"
            image_analysis_parts.append(error_msg)
    
    return "\n\n".join(image_analysis_parts), attachments, image_ids

def create_enhanced_message(text_query: str, image_analysis: str, user_id: str, past_conversation: str, recent_conversation: str):
    """Create enhanced message for AutoGen agents, explicitly referencing mem0 context."""
    
    enhanced_message = f"""
    You are a helpful agricultural advisor. Your job is to answer the farmer's query with practical, easy-to-understand, and actionable advice. Keep your response conversational and focused on steps the farmer can take immediately.

    You may be given:
    - A user query
    - An analysis of uploaded images (only if provided)
    - Context retrieved from the mem0 memory system, which provides relevant past conversations and knowledge base information using semantic search.
    - A summary of the recent conversation, which provides a short paragraph that captures what was recently discussed so the next assistant can respond appropriately.
    - Use past conversation history to understand the user's background, preferences, and any relevant prior advice. You should past conversations only if the recent conversation is not enough to understand the user's question.

    Use the **mem0 context** (provided as past conversation history) to understand the user's background, preferences, and any relevant prior advice. If **image analysis is present**, use it to improve your response. If not, ignore that section.

    ---

    USER ID: {user_id}

    MEM0 CONTEXT (Session History):
    {past_conversation}

    RECENT CONVERSATION:
    {recent_conversation}

    IMAGE ANALYSIS (optional):
    {image_analysis}

    CURRENT USER QUERY:
    {text_query}
    """
    
    return enhanced_message.strip()

def get_charlie_response(user_input):
    """Get Charlie's response using Azure OpenAI with Texas personality."""
    url = f"{AZURE_OPENAI_ENDPOINT}openai/deployments/{AZURE_OPENAI_DEPLOYMENT}/chat/completions?api-version={AZURE_OPENAI_API_VERSION}"

    headers = {
        "Content-Type": "application/json",
        "api-key": AZURE_OPENAI_API_KEY
    }

    body = {
        "messages": [
            {"role": "system", "content": "You are Charlie, a friendly, smart farm advisor with a slight Texas charm. Be helpful, clear, and warm. Use practical advice about farming and food supply."},
            {"role": "user", "content": user_input}
        ]
    }

    response = azure_openai_client.chat.completions.create(
        model=AZURE_OPENAI_DEPLOYMENT,
        messages=body["messages"],
        max_tokens=400
    )
    result = response.json()
    result = json.loads(result)

    print("\n🔍 Raw response from Azure OpenAI:\n", json.dumps(result, indent=2))

    if "choices" in result and len(result["choices"]) > 0:
        return result["choices"][0]["message"]["content"]
    else:
        return "Well, bless your heart, I'm having a bit of trouble getting through right now. Let's try that again, partner."


async def handle_voice_conversation(websocket: WebSocket, payload: dict):
    """Handle voice conversation requests."""
    user_id = payload.get("user_id", "default_user")
    session_id = payload.get("session_id", "default_session")
    audio_b64 = payload.get("audio")
    audio_format = payload.get("audio_format", "webm")
    
    if not audio_b64:
        await websocket.send_text(json.dumps({"type": "error", "content": "No audio data received."}))
        return
    
    try:
        # Decode and save audio
        audio_bytes = base64.b64decode(audio_b64)
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{audio_format}") as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        
        # Convert to wav for Azure Speech if needed
        wav_path = tmp_path
        if audio_format != "wav":
            wav_path = tmp_path + ".wav"
            audio = AudioSegment.from_file(tmp_path, format=audio_format)
            audio.export(wav_path, format="wav")
        
        # Transcribe audio
        speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_SPEECH_REGION)
        audio_input = speechsdk.AudioConfig(filename=wav_path)
        speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_input)
        result = speech_recognizer.recognize_once()
        
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            transcript = result.text
            print(f"[VOICE CONVERSATION] User '{user_id}' transcribed: {transcript}")  # Log the transcript for debugging

            session_storage = SessionStorageManager(max_messages_per_chunk=100)
            
            # Store user voice message in session storage
            session_storage.add_message(
                session_id=session_id,
                role="user",
                content=transcript,
                user_id=user_id
            )
            
            # Get Charlie's response
            charlie_response = get_charlie_response(transcript)
            print(f"[VOICE CONVERSATION] Charlie's response: {charlie_response}")
            
            # Clean text for TTS
            clean_response = clean_for_tts(charlie_response)
            
            # Convert to speech
            audio_b64 = text_to_speech_base64(clean_response)
            
            # Send response back to frontend
            await websocket.send_text(json.dumps({
                "type": "voice_response",
                "text": clean_response,
                "original": charlie_response,
                "audio": audio_b64,
                "transcript": transcript
            }))
            
            # Store assistant's voice response in session storage
            session_storage.add_message(
                session_id=session_id,
                role="assistant",
                content=clean_response,
                user_id=user_id
            )
            
        elif result.reason == speechsdk.ResultReason.NoMatch:
            error_text = "I couldn't understand what you said. Could you please try again?"
            audio_b64 = text_to_speech_base64(error_text)  # Use Jenny's voice
            await websocket.send_text(json.dumps({
                "type": "voice_response",
                "text": error_text,
                "original": error_text,
                "audio": audio_b64,  # Send Jenny's voice
                "transcript": "[No speech could be recognized]"
            }))
        else:
            error_text = "There was an issue with speech recognition. Please try again."
            audio_b64 = text_to_speech_base64(error_text)  # Use Jenny's voice
            await websocket.send_text(json.dumps({
                "type": "voice_response",
                "text": error_text,
                "original": error_text,
                "audio": audio_b64,  # Send Jenny's voice
                "transcript": "[Speech recognition error]"
            }))
            
    except Exception as e:
        print(f"[VOICE CONVERSATION] Error: {e}")
        error_text = "Sorry, there was an error processing your voice input. Please try again."
        audio_b64 = text_to_speech_base64(error_text)  # Use Jenny's voice for errors too
        await websocket.send_text(json.dumps({
            "type": "voice_response",
            "text": error_text,
            "original": error_text,
            "audio": audio_b64,  # Send Jenny's voice instead of None
            "transcript": f"[Error: {str(e)}]"
        }))
    finally:
        for path in [tmp_path, wav_path if 'wav_path' in locals() else None]:
             if path and os.path.exists(path):
                for attempt in range(10):                         # retry up to 5 times
                    try:
                        os.remove(path)
                        break
                    except PermissionError:
                        time.sleep(0.1)                    # give Windows a moment to release
                    except Exception as e:
                        print(f"❌ Error deleting {path}: {e}")
                        break
        # Clean up temporary files
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.remove(tmp_path)
        if 'wav_path' in locals() and wav_path != tmp_path and os.path.exists(wav_path):
            os.remove(wav_path)

async def handle_audio_message(websocket: WebSocket, payload: dict):
    """Handle audio messages for main chat (transcription only)."""
    user_id = payload.get("user_id", "default_user")
    audio_b64 = payload.get("audio")
    audio_format = payload.get("audio_format", "webm")
    
    if not audio_b64:
        await websocket.send_text(json.dumps({"type": "error", "content": "No audio data received."}))
        return
    
    # Decode and save audio
    audio_bytes = base64.b64decode(audio_b64)
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{audio_format}") as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name
    
    try:
        # Convert to wav for Azure Speech if needed
        wav_path = tmp_path
        if audio_format != "wav":
            wav_path = tmp_path + ".wav"
            audio = AudioSegment.from_file(tmp_path, format=audio_format)
            audio.export(wav_path, format="wav")
        
        # Transcribe
        speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_SPEECH_REGION)
        audio_input = speechsdk.AudioConfig(filename=wav_path)
        speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_input)
        result = speech_recognizer.recognize_once()
        
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            transcript = result.text
            print("Recognized: {}".format(result.text))
        elif result.reason == speechsdk.ResultReason.NoMatch:
            transcript = "[No speech could be recognized]"
            print("No speech could be recognized: {}".format(result.no_match_details))
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            print("Speech Recognition canceled: {}".format(cancellation_details.reason))
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                print("Error details: {}".format(cancellation_details.error_details))
            transcript = "[Speech recognition was canceled]"
        else:
            transcript = "[Could not transcribe audio]"
        
        print(f"[AUDIO TRANSCRIPTION] User '{user_id}': {transcript}") ## Log the transcript for debugging
        
        # Send transcribed text to frontend for user to edit
        await websocket.send_text(json.dumps({
            "type": "transcribed_audio", 
            "text": transcript
        }))
        
    except Exception as e:
        await websocket.send_text(json.dumps({"type": "error", "content": f"Audio processing error: {e}"}))
    finally:
       for path in [tmp_path, wav_path if 'wav_path' in locals() else None]:
            if path and os.path.exists(path):
                for attempt in range(10):
                    try:
                        os.remove(path)
                        break
                    except PermissionError:
                        time.sleep(0.1)
                    except Exception as e:
                        print(f"❌ Error deleting {path}: {e}")
                        break

def summarize_conversation_mem0(user_message: str, agent_response: str, image_analysis: str):
    """Summarize the conversation for mem0."""
    prompt = f"""
        Given the following conversation between a user and an assistant, do two things:
        1. Write a concise 1-2 sentence summary of the main issue and advice.
        2. List the main agricultural topics or keywords discussed, as a Python list of strings, give me a list that will be used to search for relevant memories.
        3. If there is no image analysis, do not mention it in the summary.

        Conversation:
        User: {user_message}
        Assistant: {agent_response}
        {f"Image Analysis: {image_analysis}" if image_analysis else ""}

        Return your answer as a JSON object with 'summary' and 'topics' fields.
        """
    response = azure_openai_client.chat.completions.create(
        model=AZURE_OPENAI_DEPLOYMENT,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        max_tokens=400
    )
    return response

def recent_conversation_summary(recent_conversation):
    """Summarize the recent conversation."""
    prompt = f"""You are a memory assistant for an agricultural chatbot.

        Your job is to summarize the last few conversation exchanges between the farmer and the assistant. The goal is to provide a short paragraph that captures what was recently discussed so the next assistant can respond appropriately.

        Focus on:
        - The user’s most recent concern, question, or action  
        - Crops, animals, or farming topics mentioned  
        - Any specific issues (e.g., diseases, pests, watering)  
        - Advice already provided or actions suggested  
        - Any user location or background information that was revealed  

        Avoid greetings or irrelevant small talk unless it's important to understanding the context.

        ---

        RECENT CONVERSATION:
        {recent_conversation}

        ---

        Return your summary in **one short paragraph** under 100 words. Do not include any other text.
    """
    response = azure_openai_client.chat.completions.create(
        model=AZURE_OPENAI_DEPLOYMENT,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=400
    ) 

    return response


async def handle_text_image_message(websocket: WebSocket, payload: dict):
    """Handle text and image messages for main chat."""
    try:
        # We define a temporary async function to wrap the chat logic.
        async def chat_task():
            # Get user query from the payload
            text_query = payload.get("text", "")
            images = payload.get("images", [])
            user_id = payload.get("user_id", "default_user")
            session_id = payload.get("session_id", "default_session")
            
            print(f"🚀 Processing query: '{text_query}' with {len(images)} images.")
            

            # Process images if they exist
            image_analysis, attachments, image_ids = "", [], []
            if images:
                image_analysis, attachments, image_ids = await process_images_with_gpt4o(images, text_query, user_id)
            
             # --- NEW: Get relevant memories using mem0 ---
            print(f"--- Searching memories for user '{user_id}' with query '{text_query}' ---")
            search_results = memory_client.search(query=text_query, user_id=user_id, limit=5)
        
            # Format the memories into a string for the prompt
            past_conversation = "No relevant past conversations found."
            if search_results and 'results' in search_results:
            # We reverse the results to get chronological order for the prompt
                relevant_memories = reversed(search_results['results']) 
                past_conversation = "\n".join([m['memory'] for m in relevant_memories])

            session_storage = SessionStorageManager(max_messages_per_chunk=100)
            recent_conversation = session_storage.get_n_messages(session_id, 10)


            # Get the number of tokens in the past conversation
            encoding = encoding_for_model("gpt-4o")
            num_tokens = len(encoding.encode(str(recent_conversation)))
            #if num_tokens > 300:
            #    recent_conversation = recent_conversation_summary(recent_conversation).choices[0].message.content
            
            # Store user's query in session storage
            session_storage.add_message(
                session_id=session_id,
                role="user",
                content=text_query,
                user_id=user_id,
                attachments=attachments
            )


            enhanced_message = create_enhanced_message(text_query, image_analysis, user_id, past_conversation, recent_conversation)
            agent_router = AgentRouter()
            result = await agent_router.process_query(enhanced_message, websocket)

            # # Clear UI
            # await websocket.send_text(json.dumps({"type": "clear_agent_status"}))

            # Get final response
            if result["success"]:
                final_advice_text = result["final_response"]
                print(f"✅ Used specialist: {result.get('specialist_used', 'Unknown')}")
            else:
                final_advice_text = result["final_response"]  # Error message
                print(f"❌ Router error: {result.get('error', 'Unknown error')}")
                
                
            audio_b64 = text_to_speech_base64(final_advice_text)
            final_data = {
                "type": "final_answer",
                "content": final_advice_text,
                "audio": audio_b64,
            }


            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.send_text(json.dumps(final_data))
            
            # Store assistant's final response in session storage
            session_storage.add_message(
                session_id=session_id,
                role="assistant",
                content=final_advice_text,
                user_id=user_id
            )

            print("--- Saving memories to mem0 ---")

            summary = final_advice_text

            memory_client.add(
                summary,
                user_id=user_id,
                run_id=session_id,
                metadata = {
                    # "topics": topics
                })
            print(f"--- Saved summary to mem0 ---")


        # Now, run the entire chat task with a timeout
        await asyncio.wait_for(chat_task(), timeout=60.0)

    except asyncio.TimeoutError:
        print("❌ --- AutoGen chat TIMED OUT! --- ❌")
        error_data = {"type": "error", "content": "The consultation is taking too long. Please try rephrasing."}
        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.send_text(json.dumps(error_data))
    except Exception as e:
        error_msg = f"An error occurred during the agent workflow: {e}"
        print(f"❌ {error_msg}")
        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.send_text(json.dumps({"type": "error", "content": str(e)}))
            await websocket.send_text(json.dumps({"type": "conversation_complete"}))

# =============================================================================
# HEALTH CHECK ENDPOINT
# =============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint for Docker and load balancers."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    # Use environment variables for Azure deployment
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 8000))
    
    uvicorn.run("backend:app", host=host, port=port, reload=False) 
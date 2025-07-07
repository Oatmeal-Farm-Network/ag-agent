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
import os
import re
import json
import asyncio
import tempfile
import base64
from datetime import datetime
import time

# Third-party imports
import uvicorn
import autogen
import requests
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.websockets import WebSocketState
from fastapi.responses import Response
from fastapi import Body
from pydantic import BaseModel
from database_module.cosmos_retriever import add_multimodal_memory_to_cosmos

# Azure services
import azure.cognitiveservices.speech as speechsdk
from pydub import AudioSegment

# Local project imports
from config import (
    autogen_llm_config_list, EXPERT_ADVISOR_NAME, USER_PROXY_NAME,
    SEARCHER_NAME, PROCESSOR_NAME, SOIL_NAME, NUTRITION_NAME,
    WEATHER_NAME, LIVESTOCK_BREED_NAME
)
from autogen_module.agents import all_agents

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
# HELPER FUNCTIONS
# =============================================================================

def extract_final_advice(autogen_messages):
    """Extract the final advice from AutoGen conversation messages."""
    if not autogen_messages:
        return None
    
    for msg in reversed(autogen_messages):
        if msg.get("name") == EXPERT_ADVISOR_NAME:
            content = msg.get("content", "").strip()
            if content:
                return re.sub(r'\s*TERMINATE\s*$', '', content, flags=re.IGNORECASE).strip()
    return None

def robust_speaker_selection(last_speaker: autogen.Agent, groupchat: autogen.GroupChat) -> autogen.Agent:
    """
    A resilient method to select the next speaker and prevent conversation stalls.
    
    Args:
        last_speaker: The agent that just spoke
        groupchat: The group chat instance
        
    Returns:
        The next agent to speak
    """
    messages = groupchat.messages
    
    # If the last message is from the user, start the workflow
    if last_speaker.name == USER_PROXY_NAME:
        return groupchat.agent_by_name(SEARCHER_NAME)
        
    # If the last message contains "TERMINATE", the conversation is over
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

    # If the last speaker is in our defined workflow, get the next one
    if next_speaker_name := workflow.get(last_speaker.name):
        return groupchat.agent_by_name(next_speaker_name)
    
    # Fallback logic - route to Lead Advisor to conclude
    if last_speaker.name != EXPERT_ADVISOR_NAME:
        print(f"--- [WARN] Unexpected speaker '{last_speaker.name}'. Defaulting to LeadAgriculturalAdvisor. ---")
        return groupchat.agent_by_name(EXPERT_ADVISOR_NAME)

    # If the Lead Advisor just spoke, end the conversation
    return groupchat.agent_by_name(USER_PROXY_NAME)

# =============================================================================
# STREAMING GROUP CHAT CLASSES
# =============================================================================

class StreamingGroupChatManager(autogen.GroupChatManager):
    """Custom GroupChatManager that streams agent steps over WebSocket."""
    
    def __init__(self, groupchat, websocket, **kwargs):
        super().__init__(groupchat, **kwargs)
        self.websocket = websocket

    async def a_run_chat(self, messages, sender, config=None):
        """Override the main chat loop to send UI notifications."""
        for i in range(self.groupchat.max_round):
            
            
            # Select the next speaker
            speaker = self.groupchat.select_speaker(sender, self.groupchat)
            
            # Send the "agent is working" step to the UI before the agent runs
            await self._send_step_to_ui(speaker.name)

            # Let the speaker generate a reply
            reply = await speaker.a_generate_reply(messages, sender=self.groupchat, config=config)

            if reply is None:
                break  # Chat finished
                
            # Broadcast the reply to all other agents
            self.a_broadcast(reply, sender=speaker)
            messages.append(reply)
            
            # Check for termination
            if "TERMINATE" in str(reply.get("content", "")):
                break
        
        return True, None

    async def _send_step_to_ui(self, agent_name: str):
        """Send the 'agent_step' message to the frontend."""
        if agent_name == USER_PROXY_NAME:
            return
        try:
            step_data = {
                "type": "agent_step",
                "agent_name": agent_name
            }
            print(f"--> Sending agent_step for: {agent_name}")
            if self.websocket.client_state == WebSocketState.CONNECTED:
                await self.websocket.send_text(json.dumps(step_data))
                await asyncio.sleep(0.1)  # Small delay for the UI to update
        except Exception as e:
            print(f"--- Error sending agent step: {e} ---")

class StreamingGroupChat(autogen.GroupChat):
    """A custom GroupChat that streams agent steps over a WebSocket."""
    
    def __init__(self, websocket: WebSocket, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.websocket = websocket
        self.loop = asyncio.get_running_loop()
        self.streaming_tasks = []

    def append(self, message: dict, speaker: autogen.Agent):
        """Override append to handle streaming tasks."""
        super().append(message, speaker)
        
        # Create a task to stream the message to UI
        task = self.loop.create_task(self._stream_message_to_ui(speaker))
        self.streaming_tasks.append(task)

    async def _stream_message_to_ui(self, speaker: autogen.Agent):
        """Stream agent messages to the UI."""
        if speaker.name == USER_PROXY_NAME:
            return  # Don't stream farm_query_relay
        try:
            if self.websocket.client_state == WebSocketState.CONNECTED:
                step_data = {"type": "agent_step", "agent_name": speaker.name}
                await self.websocket.send_text(json.dumps(step_data))
                await asyncio.sleep(0.1)  # Brief delay for UI processing
        except Exception as e:
            print(f"❌ CRITICAL ERROR in _stream_message_to_ui: {e.__class__.__name__}: {e}")

# =============================================================================
# VOICE CONVERSATION FUNCTIONS
# =============================================================================

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

    response = requests.post(url, headers=headers, json=body)
    result = response.json()

    print("\n🔍 Raw response from Azure OpenAI:\n", json.dumps(result, indent=2))

    if "choices" in result and len(result["choices"]) > 0:
        return result["choices"][0]["message"]["content"]
    else:
        return "Well, bless your heart, I'm having a bit of trouble getting through right now. Let's try that again, partner."

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
    from config import embedding_client
    
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
            return embedding_client.chat.completions.create(
                model="gpt-4o",
                messages=[{
                    "role": "user",
                    "content": content
                }],
                max_tokens=500
            )
        
        response = await asyncio.to_thread(call_gpt4o)
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"Error calling GPT-4o: {e}")
        return f"Unable to analyze image: {str(e)}"

async def process_images_with_gpt4o(images: list, text_query: str, user_id: str):
    """Process images with GPT-4o and store in Cosmos DB."""
    from database_module.cosmos_retriever import add_image_reference_to_cosmos #Import the function to add image reference to Cosmos DB
    
    image_analysis_parts = []
    image_ids = []
    
    for img in images:
        try:
            print(f"--- Processing image: {img['name']} ---")
            
            # Analyze image with GPT-4o
            analysis = await analyze_single_image_with_gpt4o(img['data'], text_query)
            print(f"--- GPT-4o analysis: {analysis[:100]}... ---")
            
            image_analysis_parts.append(analysis)
            
            # Store image in Blob Storage and reference in Cosmos DB
            image_bytes = base64.b64decode(img['data']) # <-- Decode the base64 string to bytes
            
            image_id = add_image_reference_to_cosmos(
                image_bytes=image_bytes, # <-- Pass the raw bytes with the correct parameter name
                image_description=analysis,
                user_id=user_id,
                metadata={
                    "file_name": img['name'],
                    "file_size": len(image_bytes), # Use the size of the decoded bytes
                    "original_query": text_query
                }
            )
            
            if image_id:
                image_ids.append(image_id)
                print(f"--- Image stored with ID: {image_id} ---")
            else:
                print(f"--- WARNING: No image_id returned for {img['name']} ---")
                
        except Exception as e:
            print(f"Error processing image {img['name']}: {e}")
            error_msg = f"Error analyzing image {img['name']}: {str(e)}"
            image_analysis_parts.append(error_msg)
    
    return "\n\n".join(image_analysis_parts), image_ids

def create_enhanced_message(text_query: str, image_analysis: str, user_id: str, image_ids: list):
    """Create enhanced message for AutoGen agents."""
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



# speaker icon logic

@app.post("/api/text-to-speech")
async def text_to_speech_endpoint(payload: TextToSpeechRequest = Body(...)):
    """
    Receives text and returns the synthesized speech as an MP3 audio stream.
    """
    text_to_speak = payload.text
    if not text_to_speak:
        raise HTTPException(status_code=400, detail="No text provided")

    # 1. Configure the speech SDK for Azure
    speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_SPEECH_REGION)
    speech_config.speech_synthesis_voice_name = "en-US-AriaNeural"
    speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3)

    
    # 2. IMPORTANT: Configure audio to be sent to an in-memory stream, not the server's speakers.
    audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=False)
    
    # 3. Create the synthesizer
    print(f"Using voice: {speech_config.speech_synthesis_voice_name}")
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
   

    # 4. Define the blocking speech synthesis call
    def synthesize():
        return synthesizer.speak_text_async(text_to_speak).get()

    # 5. Run the blocking call in a separate thread to avoid freezing the server
    result = await asyncio.to_thread(synthesize)

    # 6. Process the result and return the audio data
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        audio_data = result.audio_data
        # Return the raw MP3 data with the correct content type for the browser
        return Response(content=audio_data, media_type="audio/mpeg")
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print(f"Speech synthesis canceled: {cancellation_details.reason}")
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print(f"Error details: {cancellation_details.error_details}")
        raise HTTPException(status_code=500, detail="Speech synthesis failed")
    
    raise HTTPException(status_code=500, detail="An unknown error occurred during speech synthesis")

# =============================================================================
# WEBSocket ENDPOINT
# =============================================================================

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for chat and voice conversations."""
    await websocket.accept()
    
    # Get user proxy agent
    user_proxy = next((agent for agent in all_agents if agent.name == USER_PROXY_NAME), None)
    if not user_proxy:
        await websocket.send_text(json.dumps({"type": "error", "content": "UserProxyAgent not found."}))
        await websocket.close()
        return

    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)

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
            await handle_text_image_message(websocket, payload, user_proxy)

    except WebSocketDisconnect:
        print("Client disconnected.")
    except Exception as e:
        print(f"An error occurred in the WebSocket endpoint: {e}")

async def handle_voice_conversation(websocket: WebSocket, payload: dict):
    """Handle voice conversation requests."""
    user_id = payload.get("user_id", "default_user")
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


async def handle_text_image_message(websocket: WebSocket, payload: dict, user_proxy):
    """Handle text and image messages for main chat."""
    try:
        # We define a temporary async function to wrap the chat logic.
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

            # Set up the chat
            groupchat = StreamingGroupChat(
                websocket=websocket, agents=all_agents, messages=[], max_round=15, 
                speaker_selection_method=robust_speaker_selection
            )
            manager = autogen.GroupChatManager(
                groupchat=groupchat, llm_config={"config_list": autogen_llm_config_list}
            )
            
            # Run the main agent conversation
            await user_proxy.a_initiate_chat(manager, message=enhanced_message)
            
            # --- Clear UI and Send Final Answer ---
            try:
                for task in groupchat.streaming_tasks:
                    if not task.done(): task.cancel()
                await websocket.send_text(json.dumps({"type": "clear_agent_status"}))
            except Exception as e:
                print(f"--- [WARN] Error clearing streaming tasks: {e} ---")

            final_advice = extract_final_advice(groupchat.messages)
            final_advice_text = final_advice or "The consultation has concluded."
            audio_b64 = text_to_speech_base64(final_advice_text)
            final_data = {
                "type": "final_answer",
                "content": final_advice_text,
                "audio": audio_b64,
            }
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.send_text(json.dumps(final_data))
                
            # ===============================================================
            # === CORRECT LOCATION: Save history as the LAST step inside chat_task ====
            # ===============================================================
            print("--- Saving conversation to chat history ---")

            print(f"--- DEBUG: image_ids being passed: {image_ids} ---")
            add_multimodal_memory_to_cosmos(
                text_to_save=text_query,
                user_id=user_id,
                image_ids=image_ids if image_ids else [],  # Ensure it's always a list
                audio_ids=[]
                )
            # ===============================================================
            

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

# utilities_module/audio_utils.py
# Contains functions related to audio processing and storage.

import azure.cognitiveservices.speech as speechsdk
from config import speech_config, AUDIO_BLOB_CONTAINER_NAME
from .blob_utils import upload_file_to_blob
from .memory_processor import add_text_memory

def process_audio(audio_bytes: bytes, user_id: str, session_id: str) -> tuple[str, str]:
    """Processes audio: uploads, transcribes, and creates a memory."""
    blob_url = upload_file_to_blob(AUDIO_BLOB_CONTAINER_NAME, audio_bytes, "wav")
    if not blob_url:
        return None, "Failed to upload audio."

    try:
        audio_config = speechsdk.audio.AudioConfig(stream=speechsdk.audio.PushAudioInputStream())
        speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
        
        stream = audio_config.stream
        stream.write(audio_bytes)
        stream.close()

        result = speech_recognizer.recognize_once_async().get()
        transcription = result.text if result.reason == speechsdk.ResultReason.RecognizedSpeech else "Could not transcribe audio."
    except Exception as e:
        transcription = f"Error during transcription: {e}"
        
    add_text_memory(text_content=transcription, user_id=user_id, session_id=session_id)
    return blob_url, transcription
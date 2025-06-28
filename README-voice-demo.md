# Charlie 1.0 Voice Assistant (Azure GPT + TTS)

This module enables Charlie to speak using Azure GPT-4o for natural conversation and Azure TTS (Text-to-Speech) for voice responses. It's a standalone prototype, separate from the main ag-agent chatbot.

---

## Features
- GPT-4o integration via Azure OpenAI
- Voice output using Azure Speech Services (TTS)
- Markdown/hashtag cleanup for clean, natural speech
- Can run locally or in a Docker container

---

## Setup Instructions

### 1. Clone & enter the project
```bash
git clone https://github.com/Oatmeal-Farm-Network/ag-agent.git
cd ag-agent
```

### 2. Set up Python environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Add your Azure credentials in `charlie_voice_demo.py`
```python
AZURE_OPENAI_API_KEY = "your-key"
AZURE_OPENAI_ENDPOINT = "https://your-resource.openai.azure.com/"
AZURE_OPENAI_DEPLOYMENT = "gpt-4o"
AZURE_OPENAI_API_VERSION = "2025-01-01-preview"

speech_key = "your-speech-key"
speech_region = "eastus"
```

### 4. Run the demo
```bash
python charlie_voice_demo.py
```

Ask a question like:
```
What should I plant in Texas this July?
```

Charlie will respond and speak her answer out loud.

---

## Docker (Optional)

To build and run this module inside Docker:
```bash
docker build -f Dockerfile.voice -t charlie-voice-demo .
docker run -it charlie-voice-demo
```

### ⚠️ Audio Limitation in Docker
Audio playback (live speech) may not work inside Docker due to lack of audio drivers in containers. If you get an error like:
```
SPXERR_AUDIO_SYS_LIBRARY_NOT_FOUND
```
It means the container cannot access your Mac’s sound system.

✅ Workaround: Run the script locally (`python charlie_voice_demo.py`) for full voice playback.

Alternatively, update the `speak_text()` function to output audio to a file (`charlie_output.wav`) instead of trying to play it live.

---

## Notes
- This is a voice-only assistant prototype
- Not connected to UI or chatbot flow yet
- Can be integrated into the main ag-agent project if needed

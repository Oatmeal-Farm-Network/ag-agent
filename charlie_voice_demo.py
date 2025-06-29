import openai
import json
import re
import requests  
import azure.cognitiveservices.speech as speechsdk

## GPT Config (Azure OpenAI)
AZURE_OPENAI_ENDPOINT = "https://oatmealopenai.openai.azure.com/"
AZURE_OPENAI_DEPLOYMENT = "gpt-4o"
AZURE_OPENAI_API_KEY = "AZURE_OPENAI_API_KEY"
AZURE_OPENAI_API_VERSION = "2025-01-01-preview"

# TTS Config
speech_key = "AZURE_SPEECH_KEY"
speech_region = "eastus"

def get_charlie_response(user_input):
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

    print("\n🔍 Raw response from Azure OpenAI:\n", json.dumps(result, indent=2))  # Optional: helpful for debugging

    if "choices" in result and len(result["choices"]) > 0:
        return result["choices"][0]["message"]["content"]
    else:
        return "Sorry, I couldn’t get a response from Charlie."


def clean_for_tts(text):
    import re

    # Remove lines that start with one or more '#' symbols (Markdown headers like ### Title)
    text = re.sub(r'^\s*#{1,6}\s*.*$', '', text, flags=re.MULTILINE)

    # Remove inline hashtags like "#crops"
    text = re.sub(r'#\w+', '', text)

    # Remove the word "hashtag" itself if GPT writes it out
    text = re.sub(r'\bhashtag\b', '', text, flags=re.IGNORECASE)

    # Remove bold and italic markdown formatting
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)

    # Remove markdown-style links and plain URLs
    text = re.sub(r'\[.*?\]\(.*?\)', '', text)
    text = re.sub(r'http\S+', '', text)

    # Remove numbered list prefixes like "1. ", "2. "
    text = re.sub(r'^\s*\d+\.\s*', '', text, flags=re.MULTILINE)

    # Collapse multiple spaces and trim
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def speak_text(text):
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
    speech_config.speech_synthesis_voice_name = "en-US-JennyNeural"
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)
    synthesizer.speak_text_async(text).get()

if __name__ == "__main__":
    question = input("Ask Charlie a question: ")
    answer = get_charlie_response(question)
    print("Charlie says:", answer)
    speak_text(clean_for_tts(answer))

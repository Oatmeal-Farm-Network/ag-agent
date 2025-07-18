from openai import AzureOpenAI
import json
import os
from dotenv import load_dotenv

load_dotenv()   

vision_client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        azure_endpoint=os.getenv("AZURE_OPENAI_API_BASE")
    )

user_message = "My apple trees have dark spots on the leaves and fruit. What should I do?"
agent_response = "It sounds like apple scab. Prune affected parts, apply fungicide, and monitor regularly."

prompt = f"""
Given the following conversation between a user and an assistant, do two things:
1. Write a concise 1-2 sentence summary of the main issue and advice.
2. List the main agricultural topics or keywords discussed, as a Python list of strings.

Conversation:
User: {user_message}
Assistant: {agent_response}

Return your answer as a JSON object with 'summary' and 'topics' fields.
"""

response = vision_client.chat.completions.create(
    model=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"),
    messages=[{"role": "user", "content": prompt}],
    max_tokens=200,
    temperature=0.3,
    stop=None,
    response_format={"type": "json_object"}
)

# Parse the LLM's output as JSON
output_text = response.choices[0].message.content
print("Raw LLM output:", output_text)

try:
    result = json.loads(output_text)
    summary = result.get("summary", "")
    topics = result.get("topics", [])
except Exception as e:
    print("Error parsing LLM output:", e)
    summary = output_text
    topics = []

print("Summary:", summary)
print("Topics:", topics)
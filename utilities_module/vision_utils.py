# utilities_module/vision_utils.py
# Contains functions related to image processing and storage.
import base64
from config import embedding_client, CHAT_DEPLOYMENT, IMAGE_BLOB_CONTAINER_NAME
from .blob_utils import upload_file_to_blob
from .memory_processor import add_text_memory

def process_image(image_bytes: bytes, user_id: str, session_id: str) -> tuple[str, str]:
    """Processes an image: uploads, uses GPT-4V for analysis, and creates a memory."""
    blob_url = upload_file_to_blob(IMAGE_BLOB_CONTAINER_NAME, image_bytes, "png")
    if not blob_url:
        return None, "Failed to upload image."

    base64_image = base64.b64encode(image_bytes).decode('utf-8')

    try:
        response = embedding_client.chat.completions.create(
            model=CHAT_DEPLOYMENT,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe this image for an agricultural context. Note any signs of plant disease, pests, or soil condition."},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                    ]
                }
            ],
            max_tokens=300
        )
        description = response.choices[0].message.content
    except Exception as e:
        description = f"Could not analyze image with vision model: {e}"

    add_text_memory(text_content=f"Image Analysis: {description}", user_id=user_id, session_id=session_id)
    return blob_url, description
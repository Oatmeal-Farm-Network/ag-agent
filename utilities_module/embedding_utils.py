# utilities_module/embedding_utils.py
# Contains functions related to generating text embeddings.

import time
import numpy as np
import traceback
from typing import Optional
from openai import RateLimitError as OpenAIRateLimitError, APIError as OpenAIAPIError, BadRequestError as OpenAIBadRequestError
import streamlit as st

# Assuming your config.py is in the root of your project (e.g., one level above utilities_module)
# If your project structure is different, you might need to adjust the import path for config.
# For the structure agricultural_advisor_project/config.py and agricultural_advisor_project/utilities_module/embedding_utils.py
# this import should work when app.py in the root is run.
from config import embedding_client, EMBED_DEPLOYMENT

def get_embedding(text: str, retries: int = 3, delay: int = 5) -> Optional[np.ndarray]:
    """Generates embeddings for a given text using Azure OpenAI."""
    if embedding_client is None:
        print("Warning: Embedding client not initialized (from embedding_utils.py).")
        st.warning("Embedding client not initialized during get_embedding call.")
        return None
    if not text or not text.strip():
        print("Warning: Empty text provided for embedding.")
        # Consider st.warning("Empty text provided for embedding.") if user feedback is desired
        return None  # Return None for empty or whitespace-only input

    for attempt in range(retries):
        try:
            resp = embedding_client.embeddings.create(model=EMBED_DEPLOYMENT, input=[text])
            return np.array(resp.data[0].embedding, dtype=np.float32)
        except OpenAIRateLimitError as rle:
            print(f"Rate limit error during embedding (Attempt {attempt + 1}/{retries}): {rle}")
            if attempt < retries - 1:
                time.sleep(delay * (attempt + 1))
            else:
                st.warning(f"Rate limit exceeded after {retries} attempts while generating embeddings.")
        except OpenAIBadRequestError as bre:
            print(f"Bad request error during embedding: {bre}")
            st.error(f"Azure OpenAI API Bad Request (embedding): {bre}")
            return None  # Non-recoverable for this request
        except OpenAIAPIError as apie:
            print(f"API error during embedding (Attempt {attempt + 1}/{retries}): {apie}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                st.warning(f"Azure OpenAI API error after {retries} attempts (embedding): {apie}")
        except Exception as e:
            print(f"Unexpected error during embedding (Attempt {attempt + 1}/{retries}): {e}")
            detailed_traceback = traceback.format_exc()
            print(detailed_traceback) # For server-side logging
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                st.error(f"An unexpected error occurred while generating embeddings: {e}")
    print("All retries failed for embedding.")
    return None  # Failed all retries
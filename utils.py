# utils.py

# This file has general-purpose helper functions, such as generating text embeddings using Azure OpenAI 
#and an optional class for redirecting console output.

import sys
import time
import numpy as np
import traceback
from typing import Optional, List, Callable # For type hints
from openai import RateLimitError as OpenAIRateLimitError, APIError as OpenAIAPIError, BadRequestError as OpenAIBadRequestError
import streamlit as st

# Importing from config (ensure config.py is in the same directory or sys.path is configured)
from config import embedding_client, EMBED_DEPLOYMENT

class StreamlitRedirect:
    """Redirects stdout/stderr to a buffer for Streamlit display."""
    def __init__(self, stdout=True):
        self.stdout = stdout
        self.buffer = []
        if stdout:
            self.old_stdout = sys.stdout
            sys.stdout = self
        else:
            self.old_stderr = sys.stderr
            sys.stderr = self

    def write(self, text: str):
        self.buffer.append(text)
        if self.stdout:
            self.old_stdout.write(text)
        else:
            self.old_stderr.write(text)

    def flush(self):
        if self.stdout:
            self.old_stdout.flush()
        else:
            self.old_stderr.flush()

    def get_and_clear(self) -> str:
        content = "".join(self.buffer)
        self.buffer = []
        return content

def get_embedding(text: str, retries: int = 3, delay: int = 5) -> Optional[np.ndarray]:
    """Generates embeddings for a given text using Azure OpenAI."""
    if embedding_client is None:
        print("Warning: Embedding client not initialized (from utils.py).")
        st.warning("Embedding client not initialized during get_embedding call.")
        return None
    if not text or not text.strip():
        print("Warning: Empty text provided for embedding.")
        return None # Return None for empty or whitespace-only input

    for attempt in range(retries):
        try:
            resp = embedding_client.embeddings.create(model=EMBED_DEPLOYMENT, input=[text])
            return np.array(resp.data[0].embedding, dtype=np.float32)
        except OpenAIRateLimitError as rle:
            print(f"Rate limit error (Attempt {attempt+1}/{retries}): {rle}")
            if attempt < retries - 1:
                time.sleep(delay * (attempt + 1))
            else:
                st.warning(f"Rate limit exceeded after {retries} attempts for embeddings.")
        except OpenAIBadRequestError as bre:
            print(f"Bad request error (embedding): {bre}")
            st.error(f"Azure OpenAI API Bad Request (embedding): {bre}")
            return None # Non-recoverable for this request
        except OpenAIAPIError as apie:
            print(f"API error (Attempt {attempt+1}/{retries}): {apie}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                st.warning(f"Azure OpenAI API error after {retries} attempts (embedding): {apie}")
        except Exception as e:
            print(f"Unexpected error (Attempt {attempt+1}/{retries}): {e}")
            # traceback.print_exc() # For server-side logging
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                st.error(f"An unexpected error occurred generating embeddings: {e}")
    return None # Failed all retries
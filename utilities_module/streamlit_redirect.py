# utilities_module/streamlit_redirect.py
# Contains the StreamlitRedirect class for capturing stdout/stderr.

import sys
from typing import List # For type hint on self.buffer

class StreamlitRedirect:
    """Redirects stdout/stderr to a buffer, optionally for Streamlit display elsewhere."""
    def __init__(self, stdout: bool = True):
        self.stdout: bool = stdout
        self.buffer: List[str] = []
        if stdout:
            self.old_stdout = sys.stdout
            sys.stdout = self
        else:
            self.old_stderr = sys.stderr
            sys.stderr = self

    def write(self, text: str):
        self.buffer.append(text)
        if self.stdout:
            self.old_stdout.write(text) # Still write to original stdout
        else:
            self.old_stderr.write(text) # Still write to original stderr

    def flush(self):
        if self.stdout:
            self.old_stdout.flush()
        else:
            self.old_stderr.flush()

    def get_and_clear(self) -> str:
        """Returns the buffered content and clears the buffer."""
        content = "".join(self.buffer)
        self.buffer = []
        return content

    def restore(self):
        """Restores the original stdout/stderr."""
        if self.stdout and hasattr(self, 'old_stdout'):
            sys.stdout = self.old_stdout
        elif not self.stdout and hasattr(self, 'old_stderr'):
            sys.stderr = self.old_stderr
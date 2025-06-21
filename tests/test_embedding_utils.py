import pytest
import numpy as np
from unittest.mock import patch, MagicMock

# Import the function from your module that we need to test
from utilities_module.embedding_utils import get_embedding


# Test 1: The most important "Happy Path" case
@patch('utilities_module.embedding_utils.embedding_client')
def test_get_embedding_success(mock_embedding_client):
    """
    Tests that the function returns a valid NumPy array on a successful API call.
    This test mocks the external API so it runs fast and without cost.
    """
    # ARRANGE: Set up our mock to return a fake, successful response.
    # We create a fake embedding vector that our mock API will return.
    fake_embedding_vector = [0.1, 0.2, 0.3]
    
    # This MagicMock object mimics the complex response structure from OpenAI
    mock_response = MagicMock()
    mock_response.data[0].embedding = fake_embedding_vector
    mock_embedding_client.embeddings.create.return_value = mock_response

    # ACT: Run the function we are testing.
    result = get_embedding("hello world")

    # ASSERT: Check if the result is what we expect.
    assert result is not None
    assert isinstance(result, np.ndarray)
    assert result.shape == (3,) # Check if the array has 3 elements
    
    # Also, assert that our mock API was actually called once.
    mock_embedding_client.embeddings.create.assert_called_once()


# Test 2: A simple edge case for invalid input
def test_get_embedding_handles_empty_string():
    """
    Tests that the function correctly returns None when given an empty string.
    This test requires no mocking as it should never reach the API call.
    """
    # ARRANGE: No setup needed
    
    # ACT: Run the function with an empty string
    result = get_embedding("")
    
    # ASSERT: The result should be None
    assert result is None
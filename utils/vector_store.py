"""Vector store utilities for the social media post generator."""

from typing import List
from openai import OpenAI
from openai.types import VectorStore


def create_vector_store_from_file(file_paths: List[str], user_settings: dict) -> VectorStore:
    """Create a vector store from a file.
    
    Args:
        file_paths: List of file paths to create vector store from.
        user_settings: Dictionary containing user settings including API keys.
        
    Returns:
        The created vector store.
    """
    # Configure client
    client = OpenAI(api_key=user_settings.get("openai_api_key"))

    # Create a vector store from the file
    vector_store = client.vector_stores.create(name="company_context")

    # Ready the files for upload to OpenAI
    file_streams = [open(path, "rb") for path in file_paths]

    # Use the upload and poll SDK helper to upload the files, add them to the vector store,
    # and poll the status of the file batch for completion.
    file_batch = client.vector_stores.file_batches.upload_and_poll(
        vector_store_id=vector_store.id, files=file_streams
    )
    print(f"----- File batch status: {file_batch.status}")
    print(f"----- File batch ID: {file_batch.id}")

    return vector_store

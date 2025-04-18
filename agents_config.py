"""Agent configuration utilities for the social media post generator."""

from typing import Optional, List
from agents import Agent, ModelSettings, FileSearchTool
import os
from utils.vector_store import create_vector_store_from_file


def create_file_agent(name: str, instructions: str, context_file_path: str | None, 
                                  model: str, user_settings: dict) -> Optional[Agent]:
    """Create and return a company insights agent with the provided context file.
    
    Args:
        context_file_path: Optional path to a context file.
        model: The model to use for the agent.
        user_settings: Dictionary containing user settings including API keys.
        
    Returns:
        The created agent or None if creation failed.
    """
    
    if context_file_path is None: return None
    
    file_paths = [context_file_path] 
    
    # Check if the file exists
    for path in file_paths:
        if not os.path.exists(path):
            print(f"Warning: File {path} does not exist.")
            return None
    
    # Create the agent with the file search tool
    try:
        vector_store = create_vector_store_from_file(file_paths, user_settings)
        
        return Agent(
            name=name,
            instructions=instructions,
            model=model,
            tools=[
                FileSearchTool(vector_store_ids=[vector_store.id])
            ],
            model_settings=ModelSettings(
                tool_choice="required",
            ),
        )
    except Exception as e:
        print(f"Error creating company insights agent: {str(e)}")
        return None


def create_social_media_assistant(model: str, tools: List = None, 
                                  tool_choice: str = "none") -> Optional[Agent]:
    """Create a social media assistant agent.
    
    Args:
        model: The model to use for the agent.
        tools: Optional list of tools for the agent.
        tool_choice: How the agent should use tools.
        
    Returns:
        The created social media assistant agent.
    """
    return Agent(
        name="social_media_assistant",
        instructions="""
            You are a social media assistant.
            Your job is to generate a content brief for a social media post based on the user's input.
            Each brief should guide the marketing team by suggesting the right format, giving creative design 
            directions, and summarizing the key message. Adapt your suggestions to the user's goal, audience, and tone. 
            If details are missing, make reasonable assumptions.
        """,
        model=model,
        tools=tools or [],
        model_settings=ModelSettings(
            tool_choice=tool_choice,
        ),
    )

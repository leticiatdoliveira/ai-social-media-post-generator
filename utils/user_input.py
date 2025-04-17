"""User input handling utilities for the social media post generator."""

from flask import request
from werkzeug.utils import secure_filename
import os


def extract_user_settings() -> dict:
    """Extract user settings from the form data.
    
    Returns:
        Dictionary containing user settings.
    """
    openai_api_key = request.form.get('openai_api_key')
    openai_model = request.form.get('openai_model')
    scrapegraph_api_key = request.form.get('scrapegraph_api_key')

    user_settings = {
        "openai_api_key": openai_api_key,
        "openai_model": openai_model,
        "scrapegraph_api_key": scrapegraph_api_key
    }
    return user_settings


def extract_user_inputs() -> dict:
    """Extract user input from the form data.
    
    Returns:
        Dictionary containing user inputs.
    """
    # Extract user input from the form data
    subject = request.form.get('subject')
    description = request.form.get('description', '')
    platform = request.form.get('platform')
    tone = request.form.get('tone')
    include_hashtags = request.form.get('includeHashtags') == 'true'
    max_hashtags = request.form.get('maxHashtags', 5)
    
    # Extract scraping data
    enable_scraping = request.form.get('enableScraping') == 'true'
    scrape_url = request.form.get('scrapeUrl', '')
    scrape_prompt = request.form.get('scrapePrompt', 'Extract the main content from this page')

    # Prepare user input for the agent
    user_input = {
        "subject": subject,
        "description": description,
        "platform": platform,
        "tone": tone,
        "includeHashtags": include_hashtags,
        "maxHashtags": max_hashtags,
        "enableScraping": enable_scraping,
        "scrapeUrl": scrape_url,
        "scrapePrompt": scrape_prompt
    }
    return user_input


def create_prompt(user_input: dict, scraped_content: str = None) -> str:
    """Create a prompt for the social media assistant agent.
    
    Args:
        user_input: Dictionary containing user inputs.
        scraped_content: Optional content scraped from a website.
        
    Returns:
        Formatted prompt string for the agent.
    """
    prompt = f"""
        Generate a content brief for a social media post based on the following user input:
        Subject: {user_input["subject"]}
        Description: {user_input["description"]}
        Platform: {user_input["platform"]}
        Tone: {user_input["tone"]}
    """
    
    # Add scraped content if available
    if scraped_content:
        prompt += f"""
        Use the following information scraped from a website:
        {scraped_content}
        """
    
    if user_input["includeHashtags"]:
        prompt += f"""
            Include {user_input["maxHashtags"]} relevant hashtags for the post.
        """
    return prompt


def save_uploaded_file(file, upload_folder) -> str:
    """Save an uploaded file and return the path.
    
    Args:
        file: The file to save.
        upload_folder: The folder to save the file to.
        
    Returns:
        The path to the saved file.
    """
    filename = secure_filename(file.filename)
    file_path = os.path.join(upload_folder, filename)
    file.save(file_path)
    return file_path

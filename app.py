# app.py
from flask import Flask, render_template, request, jsonify
import os
import requests
from dotenv import load_dotenv
import re

# Load environment variables (optional API keys)
load_dotenv()

app = Flask(__name__, static_folder='static')

# AI provider options
AI_PROVIDER = os.getenv("AI_PROVIDER", "huggingface")  # Default to huggingface if not specified


@app.route('/')
def index():
    """Render the main page with the form."""
    return render_template('index.html')


@app.route('/generate', methods=['POST'])
def generate_content():
    """Generate content based on user inputs using selected AI API."""
    # Get form data
    data = request.json
    subject = data.get('subject')
    platform = data.get('platform')
    tone = data.get('tone')
    include_hashtags = data.get('includeHashtags')
    max_hashtags = data.get('maxHashtags', 5)  # Default to 5 if not specified
    provider = data.get('provider', AI_PROVIDER)

    # Validate inputs
    if not subject or not platform or not tone:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        # Construct prompt
        prompt = construct_prompt(subject, platform, tone, include_hashtags, max_hashtags)

        # Generate content using the selected AI provider
        if provider == "huggingface":
            content = generate_with_huggingface(prompt)
        elif provider == "openai" and os.getenv("OPENAI_API_KEY"):
            content = generate_with_openai(prompt)
        elif provider == "ollama":
            content = generate_with_ollama(prompt)
        else:
            # Fallback to local option if API providers fail
            content = generate_with_local_fallback(prompt)

        # Process the response to enforce hashtag limits and extract required inputs
        processed = process_response(content, include_hashtags, max_hashtags)

        return jsonify({
            "content": processed["content"],
            "required_inputs": processed["required_inputs"]
        })

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": "Failed to generate content"}), 500


@app.route('/generate_with_inputs', methods=['POST'])
def generate_with_inputs():
    """Generate content with additional user inputs."""
    # Get form data
    data = request.json
    subject = data.get('subject')
    description = data.get('description', '')  # Get description with empty default
    platform = data.get('platform')
    tone = data.get('tone')
    include_hashtags = data.get('includeHashtags')
    max_hashtags = data.get('maxHashtags', 5)
    additional_inputs = data.get('additionalInputs', {})
    original_content = data.get('originalContent', '')

    # Validate inputs
    if not subject or not platform or not tone:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        # Construct a prompt that includes the original content and additional inputs
        prompt = construct_prompt_with_inputs(subject, description, platform, tone, include_hashtags,
                                              max_hashtags, additional_inputs, original_content)

        # Generate content using the selected AI provider
        provider = data.get('provider', AI_PROVIDER)

        if provider == "huggingface":
            content = generate_with_huggingface(prompt)
        elif provider == "openai" and os.getenv("OPENAI_API_KEY"):
            content = generate_with_openai(prompt)
        elif provider == "ollama":
            content = generate_with_ollama(prompt)
        else:
            # Fallback to local option if API providers fail
            content = generate_with_local_fallback(prompt)

        # Process the response (no need to check for required inputs now)
        processed_content = process_response(content, include_hashtags, max_hashtags)["content"]

        return jsonify({
            "content": processed_content,
            "required_inputs": []  # No more required inputs
        })

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": "Failed to generate content"}), 500


def construct_prompt(subject, description, platform, tone, include_hashtags, max_hashtags=5):
    """Construct a prompt for the AI API based on user inputs."""
    hashtag_text = "" if not include_hashtags else f"""
    Include EXACTLY {max_hashtags} relevant hashtags at the end, not more and not less.
    Format the hashtags as #word without spaces.
    """

    # Add details from the description if provided
    description_text = f"""
    Additional details about the post: {description}
    """ if description else ""

    # Add instructions to identify missing information
    details_instruction = """
    If you need specific information to create a proper post (like product name, features, etc.), 
    DO NOT use placeholders like [Product Name]. Instead, at the end of your response,
    include a section titled "REQUIRED INPUTS:" with a list of the specific information you need.
    For example:
    REQUIRED INPUTS:
    - Product name
    - Key feature 1
    - Target audience
    """

    prompt = f"""
    Create a {platform} post about {subject} using a {tone} tone.

    The post should be appropriate for the {platform} platform in both length and style.
    {hashtag_text}
    {details_instruction}
    Make the content engaging and shareable.
    """

    return prompt


def construct_prompt_with_inputs(subject, description, platform, tone, include_hashtags, max_hashtags,
                                 additional_inputs,
                                 original_content):
    """Construct a prompt that incorporates user-provided inputs."""
    hashtag_text = "" if not include_hashtags else f"""
    Include EXACTLY {max_hashtags} relevant hashtags at the end, not more and not less.
    Format the hashtags as #word without spaces.
    """

    # Add details from the description if provided
    description_text = f"""
    Additional details about the post: {description}
    """ if description else ""

    # Construct context from additional inputs
    additional_context = ""
    if additional_inputs and len(additional_inputs) > 0:
        additional_context = "Use the following specific information in the post:\n"
        for key, value in additional_inputs.items():
            if value:  # Only add non-empty values
                additional_context += f"- {key}: {value}\n"

    # Construct the prompt
    prompt = f"""
    Create a {platform} post about {subject} using a {tone} tone.
    {description_text}
    {additional_context}

    The post should be appropriate for the {platform} platform in both length and style.
    {hashtag_text}
    Make the content engaging and shareable.

    Here was my previous attempt, but I need you to include the specific information now:
    "{original_content}"
    """

    return prompt


def process_response(content, include_hashtags, max_hashtags):
    """Process the AI response to enforce the hashtag limit and extract required inputs."""
    # Check if the response contains required inputs section
    required_inputs = []
    main_content = content

    # Extract required inputs section if present
    if "REQUIRED INPUTS:" in content:
        parts = content.split("REQUIRED INPUTS:")
        main_content = parts[0].strip()

        # Extract the required inputs list
        if len(parts) > 1:
            inputs_text = parts[1].strip()
            # Extract bullet points or numbered list items
            for line in inputs_text.split('\n'):
                line = line.strip()
                # Remove bullet points, numbers, or dashes
                cleaned_line = re.sub(r'^[\d\-\*\•\.\s]+', '', line).strip()
                if cleaned_line:
                    required_inputs.append(cleaned_line)

    # Process hashtags
    if not include_hashtags:
        # Remove any hashtags that might have been generated
        main_content = re.sub(r'#\w+', '', main_content).strip()
    else:
        # Extract all hashtags
        hashtags = re.findall(r'#\w+', main_content)

        if len(hashtags) > max_hashtags:
            # Too many hashtags, limit them
            text_without_hashtags = re.sub(r'#\w+', '', main_content).strip()
            limited_hashtags = ' '.join(hashtags[:max_hashtags])
            main_content = f"{text_without_hashtags}\n\n{limited_hashtags}"

    return {
        "content": main_content,
        "required_inputs": required_inputs
    }


def generate_with_huggingface(prompt):
    """Generate content using Hugging Face's Inference API (free tier)."""
    # Using Hugging Face's API - free for many models
    # Optional API key can be added to .env for increased rate limits
    api_key = os.getenv("HF_API_KEY", "")

    # Choose a good free model - mistralai/Mixtral-8x7B-Instruct-v0.1 is powerful and available for free
    model_id = "mistralai/Mixtral-8x7B-Instruct-v0.1"
    api_url = f"https://api-inference.huggingface.co/models/{model_id}"

    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    # Format prompt for instruction-based models
    payload = {
        "inputs": f"<s>[INST] {prompt} [/INST]",
        "parameters": {
            "max_new_tokens": 300,
            "temperature": 0.7,
            "return_full_text": False
        }
    }

    response = requests.post(api_url, headers=headers, json=payload)

    if response.status_code == 200:
        return response.json()[0]["generated_text"].strip()
    else:
        raise Exception(f"Hugging Face API error: {response.text}")


def generate_with_openai(prompt):
    """Generate content using OpenAI API (requires API key)."""
    from openai import OpenAI

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a social media content specialist."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=300,
        temperature=0.7
    )

    return response.choices[0].message.content.strip()


def generate_with_ollama(prompt):
    """Generate content using Ollama API (local or remote)."""
    # Ollama can be self-hosted for free: https://ollama.ai/
    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")

    payload = {
        "model": "mistral",  # Can be changed based on models you have pulled
        "prompt": f"You are a social media content specialist. {prompt}",
        "stream": False
    }

    response = requests.post(ollama_url, json=payload)

    if response.status_code == 200:
        return response.json()["response"].strip()
    else:
        raise Exception(f"Ollama API error: {response.text}")


def generate_with_local_fallback(prompt):
    """Simple fallback method if all API methods fail."""
    # Extremely basic generation with predefined templates
    # This is just a placeholder for a truly free fallback option

    return f"Generated content for '{prompt}' using local fallback. This is a placeholder response."

# TODO: add a description of the post we want to create, to help the AI
# TODO: add a feedback mechanism to improve the model response
# TODO: add a way to save the generated posts
# TODO: enter the image to be used in the post, and use it in the generation


if __name__ == '__main__':
    app.run(debug=True)
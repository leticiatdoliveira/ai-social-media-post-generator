# app.py
from flask import Flask, render_template, request, jsonify
import os
import requests
from dotenv import load_dotenv

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
    provider = data.get('provider', AI_PROVIDER)  # Allow selection from frontend

    # Validate inputs
    if not subject or not platform or not tone:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        # Construct prompt
        prompt = construct_prompt(subject, platform, tone, include_hashtags)

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

        return jsonify({"content": content})

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": "Failed to generate content"}), 500


def construct_prompt(subject, platform, tone, include_hashtags):
    """Construct a prompt for the AI API based on user inputs."""
    hashtag_text = "Include relevant hashtags at the end." if include_hashtags else "Do not include any hashtags."

    prompt = f"""
    Create a {platform} post about {subject} using a {tone} tone.

    The post should be appropriate for the {platform} platform in both length and style.
    {hashtag_text}
    Make the content engaging and shareable.
    """

    return prompt


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

# TODO: add limit of hashtags to create
# TODO: add a description of the post we want to create, to help the AI
# TODO: add a feedback mechanism to improve the model response
# TODO: generate more than one post, so the user can choose
# TODO: add a way to save the generated posts


if __name__ == '__main__':
    app.run(debug=True)
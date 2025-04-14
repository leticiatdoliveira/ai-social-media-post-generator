# app.py
from flask import Flask, render_template, request, jsonify
import os
import requests
from dotenv import load_dotenv
import re

from flask.json import provider

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

    prompt = f"""
    Create a {platform} post about {subject} using a {tone} tone.
    {description_text}

    The post should be appropriate for the {platform} platform in both length and style.
    {hashtag_text}
    
    Make the content engaging and shareable.
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


@app.route('/submit-feedback', methods=['POST'])
def submit_feedback():
    """Handle user feedback for improving model responses."""
    data = request.json
    original_content = data.get('original_content')
    feedback = data.get('feedback')
    provider = data.get('provider', AI_PROVIDER)

    if not original_content or not feedback:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        # Here you could store feedback in a database
        # For now, we'll just log it
        print(f"Feedback received: {feedback}")
        print(f"For content: {original_content}")

        # Extract hashtags from original content
        original_hashtags = re.findall(r'#\w+', original_content)

        # Check if feedback explicitly mentions changing hashtags
        change_hashtags = re.search(r'hashtags?|tags?', feedback.lower())

        # Set hashtag instructions based on feedback
        if change_hashtags:
            # Find the number of original hashtags to maintain
            num_hashtags = len(original_hashtags) if original_hashtags else 5
            hashtag_instructions = f"Create {num_hashtags} new relevant hashtags based on the feedback."
        else:
            hashtag_text = " ".join(original_hashtags) if original_hashtags else ""
            hashtag_instructions = f"Include these exact hashtags at the end: {hashtag_text}"

        # Generate improved content with appropriate hashtag instructions
        improved_prompt = f"""
        Original content:
        {original_content}

        User feedback:
        {feedback}

        Please generate an improved version of the original content that addresses the user's feedback.
        Maintain the same tone and platform style as the original.
        {hashtag_instructions}

        The improved content must preserve all original requirements (subject, platform, tone) while incorporating the feedback.
        """

        # Use your existing AI model to generate improved content
        # This assumes you have a function like generate_ai_content() from your original implementation
        if provider == "huggingface":
            improved_content = generate_with_huggingface(improved_prompt)
        elif provider == "ollama":
            improved_content = generate_with_ollama(improved_prompt)
        elif provider == "openai":
            improved_content = generate_with_openai(improved_prompt)
        else:
            # Fallback to local option if API providers fail
            improved_content = generate_with_local_fallback(improved_prompt)

        # Check if the improved content has hashtags
        new_hashtags = re.findall(r'#\w+', improved_content)

        # If no hashtags found but original had them, append either original or generic ones
        if not new_hashtags and original_hashtags:
            if change_hashtags:
                # Create generic hashtags based on content if feedback requested changes
                words = re.findall(r'\b\w{5,}\b', improved_content.lower())
                potential_tags = list(set([word for word in words if
                                           len(word) > 3 and word not in ['about', 'with', 'that', 'this', 'these',
                                                                          'those', 'they', 'their', 'there',
                                                                          'where', 'which', 'while']]))

                # Take up to 5 words to create hashtags
                new_tags = ["#" + word.capitalize() for word in potential_tags[:5]]
                if new_tags:
                    improved_content = f"{improved_content.strip()}\n\n{' '.join(new_tags)}"
            else:
                # Append original hashtags if feedback didn't request changes
                hashtag_text = " ".join(original_hashtags)
                improved_content = f"{improved_content.strip()}\n\n{hashtag_text}"

        return jsonify({
            "success": True,
            "message": "Thank you for your feedback!",
            "improved_content": improved_content
        })
    except Exception as e:
        print(f"Error saving feedback: {str(e)}")
        return jsonify({"error": "Failed to save feedback"}), 500


def generate_improved_content(original_content, feedback):
    """Generate improved content based on user feedback."""
    # Prepare a prompt for the AI to improve the content
    prompt = f"""
    Original content:
    {original_content}
    
    User feedback:
    {feedback}
    
    Please generate an improved version of the original content that addresses the user's feedback.
    """

    # Send to your AI provider and get the improved content
    if provider == "huggingface":
        response = generate_with_huggingface(prompt)
    elif provider == "openai" and os.getenv("OPENAI_API_KEY"):
        response = generate_with_openai(prompt)
    elif provider == "ollama":
        response = generate_with_ollama(prompt)
    else:
        # Fallback to local option if API providers fail
        response = generate_with_local_fallback(prompt)

    return response


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

# TODO: enter the image to be used in the post, and use it in the generation


if __name__ == '__main__':
    app.run(debug=True)
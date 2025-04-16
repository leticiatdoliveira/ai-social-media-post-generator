from flask import Flask, request, jsonify, render_template
import os
import re
import json
import requests
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Constants
AI_PROVIDER = os.getenv("AI_PROVIDER", "openai")  # Default to OpenAI
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
OPENAI_CHAT_COMPLETION_MODEL = "gpt-3.5-turbo"


# Make sure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """Render the main application page."""
    return render_template('index.html')


@app.route('/generate', methods=['POST'])
def generate():
    """Generate content based on user inputs using selected AI API."""
    # Get form data
    subject = request.form.get('subject')
    platform = request.form.get('platform')
    tone = request.form.get('tone')
    include_hashtags = request.form.get('includeHashtags') == 'true'
    max_hashtags = int(request.form.get('maxHashtags', 5))  
    provider = request.form.get('provider', AI_PROVIDER)
    description = request.form.get('description', '')
    
    # Get provider-specific settings
    openai_api_key = request.form.get('openai_api_key')
    openai_model = request.form.get('openai_model', 'gpt-3.5-turbo')
    hf_api_key = request.form.get('hf_api_key')
    hf_model = request.form.get('hf_model', 'mistralai/Mixtral-8x7B-Instruct-v0.1')
    ollama_url = request.form.get('ollama_url', 'http://localhost:11434/api/generate')
    ollama_model = request.form.get('ollama_model', 'mistral')

    print("---- Provider Settings -----")
    print("OpenAI API Key:", openai_api_key)
    print("OpenAI Model:", openai_model)
    print("Hugging Face API Key:", hf_api_key)
    print("Hugging Face Model:", hf_model)
    print("Ollama URL:", ollama_url)
    print("Ollama Model:", ollama_model)

    print("---- Testing Inputs -----")
    print("Subject:", subject)
    print("Description:", description)
    print("Platform:", platform)
    print("Tone:", tone)
    print("Include Hashtags:", include_hashtags)
    print("Max Hashtags:", max_hashtags)

    # Handle image upload
    image_path = None
    if 'image' in request.files:
        file = request.files['image']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)
            image_path = file_path
            print("Image Path:", image_path)

    # Validate inputs
    if not subject or not platform or not tone:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        # Construct prompt
        prompt = construct_prompt(subject, description, platform, tone, include_hashtags, max_hashtags, image_path)

        print(f"------- Generated Prompt: \n{prompt}")

        # Generate content using the selected AI provider
        if provider == "huggingface":
            # Use provided API key if available, otherwise use environment variable
            api_key = hf_api_key if hf_api_key else os.getenv("HF_API_KEY", "")
            content = generate_with_huggingface(prompt, api_key, hf_model)
        elif provider == "openai":
            # Use provided API key if available, otherwise use environment variable
            api_key = openai_api_key if openai_api_key else os.getenv("OPENAI_API_KEY")
            if api_key:  # Only proceed if we have an API key
                content = generate_with_openai(prompt, image_path, api_key, openai_model)
            else:
                # Fallback if no API key is available
                content = generate_with_local_fallback(prompt)
        elif provider == "ollama":
            content = generate_with_ollama(prompt, ollama_url, ollama_model)
        else:
            # Fallback to the local option if API providers fail
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


@app.route('/submit-feedback', methods=['POST'])
def submit_feedback():
    """Process feedback on generated content and return improved version."""
    try:
        data = request.json
        original_content = data.get('original_content', '')
        feedback = data.get('feedback', '')
        provider = request.args.get('provider', AI_PROVIDER)

        # Get provider-specific settings
        openai_api_key = request.form.get('openai_api_key')
        openai_model = request.form.get('openai_model', 'gpt-3.5-turbo')
        hf_api_key = request.form.get('hf_api_key')
        hf_model = request.form.get('hf_model', 'mistralai/Mixtral-8x7B-Instruct-v0.1')
        ollama_url = request.form.get('ollama_url', 'http://localhost:11434/api/generate')
        ollama_model = request.form.get('ollama_model', 'mistral')

        print("---- Feedback provider Settings -----")
        print("OpenAI API Key:", openai_api_key)
        print("OpenAI Model:", openai_model)
        print("Hugging Face API Key:", hf_api_key)
        print("Hugging Face Model:", hf_model)
        print("Ollama URL:", ollama_url)
        print("Ollama Model:", ollama_model)

        if not original_content or not feedback:
            return jsonify({"error": "Missing original content or feedback"}), 400

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
        """

        print(f"------- Improved Prompt: \n{improved_prompt}")

        # Use your existing AI model to generate improved content
        if provider == "huggingface":
            improved_content = generate_with_huggingface(improved_prompt, hf_api_key, hf_model)
        elif provider == "ollama":
            improved_content = generate_with_ollama(improved_prompt, ollama_url, ollama_model)
        elif provider == "openai":
            improved_content = generate_with_openai(improved_prompt, openai_api_key, openai_model)
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


def construct_prompt(subject, description, platform, tone, include_hashtags, max_hashtags=5, image_path=None):
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

    The post should be appropriate for the {platform} platform in both length and style.
    {hashtag_text}
    {description_text}
    Make sure the post is engaging and relevant to the subject.
    """

    return prompt


def process_response(content, include_hashtags, max_hashtags):
    """Process the response from the AI to ensure it meets requirements."""
    # Check if there are any missing inputs we need to ask for
    required_inputs = {}

    # Extract hashtags and check count if they were requested
    if include_hashtags:
        hashtags = re.findall(r'#\w+', content)
        if len(hashtags) > max_hashtags:
            # Too many hashtags, remove excess
            for i in range(len(hashtags) - max_hashtags):
                # Find last hashtag and remove it
                last_hash_pos = content.rfind('#')
                if last_hash_pos != -1:
                    # Find the end of this hashtag (space or newline)
                    end_pos = content.find(' ', last_hash_pos)
                    if end_pos == -1:  # No space found, might be at the end
                        end_pos = content.find('\n', last_hash_pos)

                    if end_pos == -1:  # No newline either, must be at the very end
                        content = content[:last_hash_pos].rstrip()
                    else:
                        content = content[:last_hash_pos] + content[end_pos:]

        elif len(hashtags) < max_hashtags and len(hashtags) > 0:
            # Not enough hashtags, mark as a required input
            required_inputs["hashtags"] = {
                "current": len(hashtags),
                "required": max_hashtags
            }

    return {
        "content": content,
        "required_inputs": required_inputs
    }


def generate_with_huggingface(prompt, api_key="", model_id="mistralai/Mixtral-8x7B-Instruct-v0.1"):
    """Generate content using Hugging Face's Inference API (free tier)."""
    # Using Hugging Face's API - free for many models
    # Optional API key can be added for increased rate limits
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


def generate_with_openai(prompt, image_path=None, api_key=None, model="gpt-3.5-turbo"):
    """Generate content using OpenAI API with image support if available."""
    client = OpenAI(api_key=api_key)

    if image_path and "gpt-4" in model:
        # Using GPT-4 Vision to handle the image directly
        import base64
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')

        response = client.chat.completions.create(
            model="gpt-4-vision-preview" if "vision" not in model else model,
            messages=[
                {"role": "system", "content": "You are a social media content specialist."},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
            ],
            max_tokens=300,
            temperature=0.7
        )
    else:
        # Standard GPT model without image
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a social media content specialist."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.7
        )

    print(f"Model used: {model}")

    return response.choices[0].message.content.strip()


def generate_with_ollama(prompt, ollama_url="http://localhost:11434/api/generate", model="mistral"):
    """Generate content using Ollama API (local or remote)."""
    # Ollama can be self-hosted for free: https://ollama.ai/

    payload = {
        "model": model,  # Can be changed based on models you have pulled
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

    # TODO: check how to pass context to model and review it in code (embedded etc)
    # TODO: config app to pass account to be retrieved as context (form field)
    # TODO: implement instagram data retrieving
    # TODO: check and deploy social media content draft
    # TODO: how to deploy

if __name__ == '__main__':
    app.run(debug=True)


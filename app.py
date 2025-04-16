from flask import Flask, request, jsonify, render_template
import os
import re
import json
import requests
import base64
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from openai import OpenAI
from typing import List
from pathlib import Path
import faiss
import numpy as np
import pdfplumber

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Constants
AI_PROVIDER = os.getenv("AI_PROVIDER", "openai")  # Default to OpenAI
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
OPENAI_CHAT_COMPLETION_MODEL = "gpt-3.5-turbo"
OPENAI_VISION_MODEL = "gpt-4.1-mini"

EMBEDDING_MODEL = "text-embedding-3-small"
CHUNK_SIZE = 1000

# Make sure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from a PDF file using pdfplumber."""
    full_text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            full_text += page.extract_text()
    return full_text


def load_and_split_file(file_path : str, chunk_size=CHUNK_SIZE, overlap=50) -> List[str]:
    """Load a file and split it into chunks for embedding."""
    if file_path.endswith('.pdf'):
        text = extract_text_from_pdf(file_path)
    else:
        text = Path(file_path).read_text(encoding="utf-8")
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i + chunk_size])
        chunks.append(chunk)
    return chunks


def get_embedding(text: str, model: str = EMBEDDING_MODEL) -> List[float]:
    """Get the embedding for a given text."""
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.embeddings.create(input=[text], model=model)
    return response.data[0].embedding


def build_vector_index(chunks: List[str]):
    """Build a vector index for the given chunks."""
    # Process each chunk individually to get embeddings
    vectors = [get_embedding(chunk) for chunk in chunks]
    vectors = np.array(vectors)
    index = faiss.IndexFlatL2(len(vectors[0]))
    index.add(vectors)
    return index, vectors, chunks


def retrieve_relevant_chunks(query: str, index: faiss.IndexFlatL2, vectors: np.array, chunks: List[str], top_k=5):
    """Retrieve the top k chunks that are most relevant to the query."""
    query_vector = get_embedding(query)
    _, indices = index.search(np.array([query_vector]).astype("float32"), top_k)
    return [chunks[i] for i in indices[0]]


def embed_file_context(file_path):
    """Embed the context of a file for retrieval."""
    chunks = load_and_split_file(file_path)
    index, vectors, chunks = build_vector_index(chunks)
    return index, vectors, chunks


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

    print("---- Provider Settings -----")
    print("OpenAI API Key:", openai_api_key)
    print("OpenAI Model:", openai_model)

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
        api_key = openai_api_key if openai_api_key else os.getenv("OPENAI_API_KEY")
        if api_key:
                response_data = generate_with_openai(prompt, image_path, api_key, openai_model)
                content = response_data["content"]

        # Process the response to enforce hashtag limits and extract required inputs
        processed = process_response(content, include_hashtags, max_hashtags)
        
        # Add model information to the response
        if "model_switched" in response_data and response_data["model_switched"]:
            processed["model_switched"] = response_data["model_switched"]
            processed["model_used"] = response_data["model_used"]
            processed["original_model"] = response_data["original_model"]

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
        provider = data.get('provider', AI_PROVIDER)

        # Get provider-specific settings from the JSON data
        openai_api_key = data.get('openai_api_key')
        openai_model = data.get('openai_model', 'gpt-3.5-turbo')

        print("---- Feedback provider Settings -----")
        print("OpenAI API Key:", openai_api_key)
        print("OpenAI Model:", openai_model)

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
        improved_content = generate_with_openai(improved_prompt, None, openai_api_key, openai_model)
    
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


def build_message(prompt : str, base64_image : str, retrieved_chunks : List[str]) -> List[dict]:
    """Build a message for the OpenAI API based on the prompt and image."""
    system_prompt = (
        "You are a skilled social media content creator, capable of adapting tone, "
        "style, and format to different platforms based on user instructions.\n\n"
        "Refer to this company's funnel strategy playbook to guide your response:\n\n"
        + "\n---\n".join(retrieved_chunks)
    )

    if base64_image:
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
            ]}
        ]
    else:
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]


def generate_with_openai(prompt, image_path=None, api_key=None, model="gpt-3.5-turbo"):
    """Generate content using OpenAI API with image support if available."""
    # Create client to text generation
    client = OpenAI(api_key=api_key)

    # Load context file and extract relevant chunks
    index, vectors, chunks = embed_file_context("context.pdf")
    retrieved_chunks = retrieve_relevant_chunks(prompt, index, vectors, chunks)

    # Build the message for the API
    base64_image = None
    model_switched = False
    original_model = model
    
    if image_path:
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        # Use a vision-capable model when an image is provided
        if model not in ["gpt-4-mini", "gpt-4o"]:
            model_switched = True
            model = OPENAI_VISION_MODEL  # Default to vision model when image is provided
            print(f"Switching to vision-capable model: {model}")
    
    messages = build_message(prompt, base64_image, retrieved_chunks)

    # Generate response
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=500
    )

    print(f"-------- Model used: {model}")

    # Return the content along with model information
    return {
        "content": response.choices[0].message.content.strip(),
        "model_used": model,
        "model_switched": model_switched,
        "original_model": original_model if model_switched else None
    }


if __name__ == '__main__':
    app.run(debug=True)


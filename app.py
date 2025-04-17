from typing import List, Optional
from flask import Flask, request, jsonify, render_template
import os
import tempfile
from dotenv import load_dotenv
from agents import Agent, ModelSettings, Runner, FileSearchTool, Tool
from openai import OpenAI
from openai.types.responses.response import ToolChoice
from werkzeug.utils import secure_filename

MODEL_SOCIAL_MEDIA = 'gpt-4o-mini'
MODEL_COMPANY_INSIGHTS = 'gpt-4o-mini'

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Create uploads directory if it doesn't exist
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Define routes
@app.route('/')
def index():
    """Render the main application page."""
    return render_template('index.html')

# def config_agent(user_settings : dict):
#     """Configure the social media assistant agent."""
#     if not user_settings["api_key"]:
#         user_settings["api_key"] = os.getenv("OPENAI_API_KEY")
#         print("----- API KEY NOT DEFINED BY USER \n>> Using OPENAI_API_KEY from environment variables.")
#     if not user_settings["model"]:
#         user_settings["model"] = "gpt-3.5-turbo"
#         print("----- MODEL NOT DEFINED BY USER \n>> Using default model: gpt-3.5-turbo")
#     social_media_assistant_agent.set_api_key(user_settings["api_key"])
#     social_media_assistant_agent.set_model(user_settings["model"])


def create_vector_store_from_file(file_paths: List[str]):
    """Create a vector store from a file."""
    # Configure client
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Create a vector store from the file
    vector_store = client.vector_stores.create(name="company_context")

    # Ready the files for upload to OpenAI]
    file_streams = [open(path, "rb") for path in file_paths]

    # Use the upload and poll SDK helper to upload the files, add them to the vector store,
    # and poll the status of the file batch for completion.
    file_batch = client.vector_stores.file_batches.upload_and_poll(
        vector_store_id=vector_store.id, files=file_streams
    )
    print(f"----- File batch status: {file_batch.status}")
    print(f"----- File batch ID: {file_batch.id}")

    return vector_store


def extract_user_settings() -> dict:
    """Extract user settings from the form data."""
    api_key = request.form.get('apiKey')
    model = request.form.get('model')

    user_settings = {
        "api_key": api_key,
        "model": model
    }
    return user_settings


def extract_user_inputs() -> dict:
    """Extract user input from the form data."""
    # Extract user input from the form data
    subject = request.form.get('subject')
    description = request.form.get('description', '')
    platform = request.form.get('platform')
    tone = request.form.get('tone')
    include_hashtags = request.form.get('includeHashtags') == 'true'
    max_hashtags = request.form.get('maxHashtags', 5)

    # Prepare user input for the agent
    user_input = {
        "subject": subject,
        "description": description,
        "platform": platform,
        "tone": tone,
        "includeHashtags": include_hashtags,
        "maxHashtags": max_hashtags
    }
    return user_input


def create_prompt(user_input: dict) -> str:
    """Create a prompt for the social media assistant agent."""
    prompt = f"""
        Generate a content brief for a social media post based on the following user input:
        Subject: {user_input["subject"]}
        Description: {user_input["description"]}
        Platform: {user_input["platform"]}
        Tone: {user_input["tone"]}
    """
    if user_input["includeHashtags"]:
        prompt += f"""
            Include {user_input["maxHashtags"]} relevant hashtags for the post.
        """
    return prompt


def save_uploaded_file(file) -> str:
    """Save an uploaded file and return the path."""
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    return file_path


def create_company_insights_agent(context_file_path: Optional[str] = None):
    """Create and return a company insights agent with the provided context file."""
    # Default to using context.pdf if no file is provided
    file_paths = [context_file_path] if context_file_path else ["context.pdf"]
    
    # Check if the file exists
    for path in file_paths:
        if not os.path.exists(path):
            print(f"Warning: File {path} does not exist.")
            return None
    
    # Create the agent with the file search tool
    try:
        vector_store = create_vector_store_from_file(file_paths)
        
        return Agent(
            name="company_insights",
            instructions="""
            Your job is to extract insights about the company from the provided document.
            Your goal is to provide useful information to the marketing team.
            """,
            model=MODEL_COMPANY_INSIGHTS,
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


@app.route('/generate', methods=['POST'])
async def generate_content():
    """Generate social media content based on form data."""
    try:
        # Extract user input from the form data
        user_input = extract_user_inputs()
        user_prompt = create_prompt(user_input)
        user_settings = extract_user_settings()
        
        # Check if a context file was uploaded
        context_file_path = None
        if 'context_file' in request.files and request.files['context_file'].filename:
            context_file = request.files['context_file']
            context_file_path = save_uploaded_file(context_file)
            print(f"----- Context file uploaded: {context_file_path}")
        
        # Create the company insights agent if a context file was provided
        company_insights_agent = create_company_insights_agent(context_file_path)
        
        # Create the social media assistant agent with or without the company insights tool
        tools = []
        tool_choice = "none"  # Default to no tools if no context file
        
        if company_insights_agent:
            tools = [
                company_insights_agent.as_tool(
                    tool_name="company_insights_tool",
                    tool_description="Extract company strategy insights from the provided document."
                )
            ]
            tool_choice = "required"  # Use tools if context file is provided
        
        social_media_assistant_agent = Agent(
            name="social_media_assistant",
            instructions="""
                You are a social media assistant.
                Your job is to generate a content brief for a social media post based on the user's input.
                Each brief should guide the marketing team by suggesting the right format, giving creative design directions, and summarizing the key message.
                Adapt your suggestions to the user's goal, audience, and tone. If details are missing, make reasonable assumptions.
            """,
            model=MODEL_SOCIAL_MEDIA,
            tools=tools,
            model_settings=ModelSettings(
                tool_choice=tool_choice,
            ),
        )

        # Generate content using the agent
        print("----- Asking model to generate content and waiting...")
        result = await Runner.run(starting_agent=social_media_assistant_agent, input=user_prompt)

        print(f"----- Content generated: \n>>{result.final_output}")

        # Clean up the uploaded file if it exists
        if context_file_path and os.path.exists(context_file_path):
            try:
                os.remove(context_file_path)
                print(f"----- Removed temporary file: {context_file_path}")
            except Exception as e:
                print(f"----- Error removing temporary file: {str(e)}")

        # Return the generated content
        return jsonify({
            "content": result.final_output
        })

    except Exception as e:
        return jsonify({"error": str(e)})


if __name__ == '__main__':
    app.run(debug=True)

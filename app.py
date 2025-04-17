from typing import List
from flask import Flask, request, jsonify, render_template
import os
from dotenv import load_dotenv
from agents import Agent, ModelSettings, Runner, FileSearchTool, Tool
from openai import OpenAI
from openai.types.responses.response import ToolChoice

MODEL_SOCIAL_MEDIA = 'gpt-4o-mini'
MODEL_COMPANY_INSIGHTS = 'gpt-4o-mini'

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

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


# Initialize the company's insight agent
company_insights_agent = Agent(
    name="company_insights",
    instructions="""
    Your job is to extract insights about the company from the provided document.
    Your goal is to provide useful information to the marketing team.
    """,
    model=MODEL_COMPANY_INSIGHTS,
    tools=[
        FileSearchTool(vector_store_ids=[create_vector_store_from_file(["context.pdf"]).id])
    ],
    model_settings=ModelSettings(
        tool_choice="required",
    ),
)

# Initialize the social media assistant agent
social_media_assistant_agent = Agent(
    name="social_media_assistant",
    instructions="""
        You are a social media assistant.
        Your job is to generate a content brief for a social media post based on the user's input.
        Each brief should guide the marketing team by suggesting the right format, giving creative design directions, and summarizing the key message.
        Adapt your suggestions to the user's goal, audience, and tone. If details are missing, make reasonable assumptions.
    """,
    model=MODEL_SOCIAL_MEDIA,
    tools=[
        company_insights_agent.as_tool(
            tool_name="company_insights_tool",
            tool_description="Extract company strategy insights from the provided document."
        )
    ],
    model_settings=ModelSettings(
        tool_choice="required",
    ),
)


@app.route('/generate', methods=['POST'])
async def generate_content():
    """Generate social media content based on form data."""
    try:
        # Extract user input from the form data
        user_input = extract_user_inputs()
        user_prompt = create_prompt(user_input)
        user_settings = extract_user_settings()

        # Generate content using the agent
        print("----- Asking model to generate content and waiting...")
        result = await Runner.run(starting_agent=social_media_assistant_agent, input=user_prompt)

        print(f"----- Content generated: \n>>{result.final_output}")

        # Return the generated content
        return jsonify({
            "content": result.final_output
        })

    except Exception as e:
        return jsonify({"error": str(e)})


if __name__ == '__main__':
    app.run(debug=True)

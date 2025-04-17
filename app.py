from flask import Flask, request, jsonify, render_template
import os
from dotenv import load_dotenv
from agents import Agent, Runner
import asyncio
from pydantic import BaseModel

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

@app.route('/')
def index():
    """Render the main application page."""
    return render_template('index.html')


class BriefContent(BaseModel):
    """Brief content model."""
    format: str
    design_directions: str
    caption: str
    post_legend: str
    hashtags: list[str] 


# Initialize the social media assistant agent
social_media_assistant_agent = Agent(
    name= "social_media_assistant",
    instructions="""
        You are a social media assistant.",
        Your job is to generate a content brief for a social media post based on the user's input.
        Each brief should guide the marketing team by suggesting the right format, giving creative design directions, and summarizing the key message.
        Adapt your suggestions to the user's goal, audience, and tone. If details are missing, make reasonable assumptions.
    """,
    model='gpt-3.5-turbo',
    tools=[]
)


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


def create_prompt(user_input : dict) -> str:
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


@app.route('/generate', methods=['POST'])
async def generate_content():
    """Generate social media content based on form data."""
    try:
        # Extract user input from the form data
        user_input = extract_user_inputs()
        user_prompt = create_prompt(user_input)
        #user_settings = extract_user_settings()

        # Configure the agent
        #config_agent(user_settings)

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


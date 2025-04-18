"""Main application file for the AI Social Media Post Generator."""

from flask import Flask, request, jsonify, render_template
import os
from agents import Runner
import utils.scrape as scrape
from dotenv import load_dotenv

# Import modules from our restructured application
from utils.user_input import (
    extract_user_settings,
    extract_user_inputs,
    create_prompt,
    save_uploaded_file
)
from agents_config import create_file_agent, create_social_media_assistant


# Initialize Flask app
app = Flask(__name__)

load_dotenv()

# Create a files directory if it doesn't exist
FILES_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'files')
if not os.path.exists(FILES_FOLDER):
    os.makedirs(FILES_FOLDER)
app.config['FILES_FOLDER'] = FILES_FOLDER


# Define routes
@app.route('/')
def index():
    """Render the content generation page (second step)."""
    return render_template('index.html')


@app.route('/generate', methods=['POST'])
def generate_content():  # Remove async keyword
    """Generate social media content based on form data."""
    # try:
    user_settings = extract_user_settings()
    user_input = extract_user_inputs()
    
    if not user_settings.get("openai_api_key"):
        return jsonify({"error": "OpenAI API key is missing. Please provide a valid API key."}), 400
    os.environ['OPENAI_API_KEY'] = user_settings.get("openai_api_key")
                    
    profile_scraped_content = None
    web_scraped_content = None
    
    if user_input["profileUrl"]:
        if not user_settings.get("scrapegraph_api_key"):
            return jsonify({"error": "ScrapeGraph API key is missing. Please provide a valid API key."}), 400

        # Scrape the user's profile information
        try:
            profile_scraped_content = scrape.scrape_to_json(
                api_key=user_settings.get("scrapegraph_api_key"),
                url=user_input["profileUrl"],
                prompt="Extract account information and data on its posts"
            )
        except Exception as e:
            return jsonify({"error": f"Failed to scrape profile: {str(e)}"}), 400
    
    if user_input["scrapeUrl"] and user_input["scrapePrompt"]:
        if not user_settings.get("scrapegraph_api_key"):
            return jsonify({"error": "ScrapeGraph API key is missing. Please provide a valid API key."}), 400
       
        # Scrape the user's profile information
        web_scraped_content = scrape.scrape_to_json(
            api_key=user_settings.get("scrapegraph_api_key"),
            url=user_input["scrapeUrl"],
            prompt=user_input["scrapePrompt"]
        )
            
    user_prompt = create_prompt(user_input)
    
    # Check if a context file was uploaded
    context_file_path = None
    if 'context_file' in request.files and request.files['context_file'].filename:
        context_file = request.files['context_file']
        context_file_path = save_uploaded_file(context_file, app.config['FILES_FOLDER'])
        print(f"----- Context file uploaded: {context_file_path}")
    
    # Create the company insights agent if a context file was provided
    company_insights_agent = create_file_agent(
        context_file_path=context_file_path,
        model=user_settings.get("openai_model"),
        user_settings=user_settings,
        instructions="""
        Your job is to extract insights about the company from the provided document.
        Your goal is to provide useful information to the marketing team.
        """,
        name="company_insights_agent"
    )
    
    profile_insights_agent = create_file_agent(
        context_file_path=profile_scraped_content,
        model=user_settings.get("openai_model"),
        user_settings=user_settings,
        instructions="""
        Your job is to extract insights about the target audience based on the data from this user profile.
        Your goal is to provide useful information to adapt new social media content to the audience.
        """,
        name="profile_insights_agent"
    )
    
    inspiration_agent = create_file_agent(
        context_file_path=web_scraped_content,
        model=user_settings.get("openai_model"),
        user_settings=user_settings,
        instructions="""
        Your job is to extract insights about the data that was provided.
        Your goal is to provide inspiration to a social media content creator, 
        or any content that could be relevant to social media posts.""",
        name="inspiration_agent"
    )
    
    # Create the social media assistant agent with or without the company insights tool
    tools = []
    tool_choice = "required"
    
    # Add company insights tool if agent exists
    if company_insights_agent:
        tools.append(
            company_insights_agent.as_tool(
                tool_name="company_insights_tool",
                tool_description="Extract company strategy insights."
            )
        )
        
    # Add profile insights tool if agent exists
    if profile_insights_agent:
        tools.append(
            profile_insights_agent.as_tool(
                tool_name="profile_insights_agent",
                tool_description="Extract insights about the target audience."
            )
        )
        
    # Add inspiration tool if agent exists
    if inspiration_agent:
        tools.append(
            inspiration_agent.as_tool(
                tool_name="inspiration_agent",
                tool_description="Use web available data to inspire the content."
            )
        )
    
    if not tools:
        tool_choice = "none"
    
    social_media_assistant_agent = create_social_media_assistant(
        model=user_settings.get("openai_model"),
        tools=tools,
        tool_choice=tool_choice,
    )

    # Generate content using the agent
    print("----- Asking model to generate content and waiting...")
    result = Runner.run_sync(starting_agent=social_media_assistant_agent, input=user_prompt)

    print(f"----- Content generated: \n>>{result.final_output}")

    # Clean up all files in the files directory
    for filename in os.listdir(FILES_FOLDER):
        file_path = os.path.join(FILES_FOLDER, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")

    # Return the generated content
    return jsonify({
        "content": result.final_output
    })


if __name__ == '__main__':
    app.run(debug=True)

"""Main application file for the AI Social Media Post Generator."""

from flask import Flask, request, jsonify, render_template
import os
from agents import Runner
import utils.scrape as scrape

# Import modules from our restructured application
from utils.user_input import (
    extract_user_settings,
    extract_user_inputs,
    create_prompt,
    save_uploaded_file
)
from agents_config import create_company_insights_agent, create_social_media_assistant


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
    """Render the content generation page (second step)."""
    return render_template('index.html')


@app.route('/generate', methods=['POST'])
async def generate_content():
    """Generate social media content based on form data.
    
    Returns:
        JSON response with generated content or error message.
    """
    try:
        user_settings = extract_user_settings()
        user_input = extract_user_inputs()
        
        # Initialize scraped content
        scraped_content = None
        
        # Perform scraping if enabled
        if user_input["scrapeUrl"]:
            try:
                scrapegraph_api_key = user_settings.get("scrapegraph_api_key")
                if not scrapegraph_api_key:
                    return jsonify({"error": "ScrapeGraphAI API key is required for website scraping"})
                
                # Initialize the scraper client
                client = scrape.init_client(scrapegraph_api_key)
                
                # Scrape the website
                scraped_content = scrape.scrape_website(
                    client=client,
                    url=user_input["scrapeUrl"],
                    prompt=user_input["scrapePrompt"]
                )
                print(f"----- Content scraped from {user_input['scrapeUrl']}")
            except Exception as e:
                return jsonify({"error": f"Failed to scrape website: {str(e)}"})
                
        user_prompt = create_prompt(user_input, scraped_content)
        
        # Check if a context file was uploaded
        context_file_path = None
        if 'context_file' in request.files and request.files['context_file'].filename:
            context_file = request.files['context_file']
            context_file_path = save_uploaded_file(context_file, app.config['UPLOAD_FOLDER'])
            print(f"----- Context file uploaded: {context_file_path}")
        
        # Create the company insights agent if a context file was provided
        company_insights_agent = create_company_insights_agent(
            context_file_path=context_file_path,
            model=user_settings.get("openai_model"),
            user_settings=user_settings
        )
        
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
        
        social_media_assistant_agent = create_social_media_assistant(
            model=user_settings.get("openai_model"),
            tools=tools,
            tool_choice=tool_choice
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

from scrapegraph_py import Client
from scrapegraphai.graphs import SmartScraperGraph
import json
import os
import hashlib
import time
import nest_asyncio


def init_client(api_key: str) -> Client:
    """Initialize the Scrapegraph client."""

    client = Client(api_key)

    return client


def scrape_website(client: Client, url: str, prompt: str) -> str:
    """Scrape the website using the Scrapegraph client."""

    response = client.smartscraper(
        website_url=url,
        user_prompt=prompt
    )

    return response


def init_scrapegraph_openai(api_key: str, model: str) -> dict:
    """Initialize the ScrapegraphAI client."""

    graph_config = {
        "llm": {
            "api_key": api_key,
            "model": "openai/" + model,
        },
        "verbose": True,
        "headless": True,
    }

    return graph_config


def scrape_website_openai(config: dict, url: str, prompt: str) -> str:
    """Scrape the website using the ScrapegraphAI smart scraper graph."""

    smart_scraper_graph = SmartScraperGraph(
        prompt=prompt,
        source=url,
        config=config
    )

    result = smart_scraper_graph.run()
    return result


def scrape_to_json(api_key, model, url, prompt) -> str:
    """Scrape a website and save the content to a JSON file."""

    # *************** SCRAPEGRAPH *************** #
    client = init_client(api_key)
    # Call the function directly without async handling
    scraped_content = scrape_website(
        client=client,
        url=url,
        prompt=prompt
    )
    # ******************************************* #

    # # *************** AI *************** #
    # graph_config = init_scrapegraph_openai(api_key, model)
    
    # # Call the function directly without async handling
    # scraped_content = scrape_website_openai(
    #     config=graph_config,
    #     url=url,
    #     prompt=prompt
    # )
    # # *********************************** #

    # Create directory using a reference to the project root
    # This will work regardless of where the function is called from
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(project_root, "files")
    os.makedirs(output_dir, exist_ok=True)

    # Generate a unique filename based on URL and timestamp
    url_hash = hashlib.md5(url.encode()).hexdigest()[:10]
    timestamp = int(time.time())
    filename = f"{url_hash}_{timestamp}.json"
    file_path = os.path.join(output_dir, filename)

    # Save the scraped content to a JSON file
    with open(file_path, 'w') as f:
        json.dump(scraped_content, f, indent=4)

    return file_path

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

from scrapegraph_py import Client
from scrapegraphai.graphs import SmartScraperGraph


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
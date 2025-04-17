from scrapegraph_py import Client


def init_client(api_key) -> Client:
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

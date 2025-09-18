from agno.agent import Agent
from agno.models.google import Gemini
from agno.tools.firecrawl import FirecrawlTools
from app.agents.tools.scraping_tool import scrape_psx_by_symbol
from app.agents.prompts.system_prompts import RESEARCH_AGENT_PROMPT
from app.core.config import settings

def create_research_agent() -> Agent:
    """
    Creates and configures the financial research agent.
    This agent is equipped with tools to scrape PSX data, perform detailed
    web scraping with Firecrawl, and use Google Search for contextual information.
    """
    # Configure Firecrawl tool to only enable scraping
    firecrawl_scraper = FirecrawlTools(
        api_key=settings.FIRECRAWL_API_KEY,
        enable_scrape=True,
        limit=3
    )

    # Configure the Gemini model
    # search=True enables the agent to use Google Search as a built-in tool
    model = Gemini(
        id="gemini-2.5-flash",
        api_key=settings.GOOGLE_API_KEY,
        search=True
    )

    return Agent(
        model=model,
        tools=[
            scrape_psx_by_symbol,
            firecrawl_scraper
        ],
        instructions=RESEARCH_AGENT_PROMPT,
        markdown=True,
    )

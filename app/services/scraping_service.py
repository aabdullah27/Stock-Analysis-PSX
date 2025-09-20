import os
import requests
from firecrawl import Firecrawl
from typing import List, Dict, Union
from app.core.config import settings
import asyncio

class ScrapingService:
    """
    A service dedicated to scraping data from various web sources for stock analysis.
    It handles scraping from PSX directly and uses Firecrawl for more complex sites.
    """
    def __init__(self, session_id: str):
        self.session_dir = os.path.join(settings.SCRAPING_OUTPUT_DIR, session_id)
        os.makedirs(self.session_dir, exist_ok=True)
        self.firecrawl_client = Firecrawl(api_key=settings.FIRECRAWL_API_KEY)

    def _get_stockanalysis_urls(self, symbol: str) -> Dict[str, str]:
        """Generates the dictionary of URLs to scrape for a given symbol."""
        base = "https://stockanalysis.com/quote/psx/" + symbol.lower()
        return {
            "overview": base + "/",
            "financials": base + "/financials/",
            "balance_sheet": base + "/financials/balance-sheet/",
            "cash_flow": base + "/financials/cash-flow-statement/",
            "ratios": base + "/financials/ratios/",
            "statistics": base + "/statistics/",
        }

    async def _scrape_psx(self, symbol: str) -> str:
        """Scrapes the PSX data portal using the requests library."""
        url = f"https://dps.psx.com.pk/company/{symbol.upper()}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        try:
            response = requests.get(url, headers=headers, timeout=20)
            response.raise_for_status()
            file_path = os.path.join(self.session_dir, f"{symbol.upper()}_psx.html")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(response.text)
            return file_path
        except requests.RequestException as e:
            print(f"Error scraping PSX for {symbol}: {e}")
            return ""

    async def _scrape_single_url_with_firecrawl(self, url: str, output_filename: str) -> str:
        """Uses Firecrawl to scrape a single URL and save it as markdown."""
        max_retries = 3
        for attempt_index in range(max_retries):
            try:
                # Firecrawl's scrape method is synchronous, run it in an executor
                loop = asyncio.get_running_loop()
                scraped_data = await loop.run_in_executor(
                    None,
                    lambda: self.firecrawl_client.scrape(url, formats=["markdown"], timeout=45000)
                )
                # Firecrawl Python SDK may return a dict or a Document-like object
                if isinstance(scraped_data, dict):
                    content = scraped_data.get("markdown", "")
                else:
                    content = getattr(scraped_data, "markdown", "")
                if content:
                    with open(output_filename, "w", encoding="utf-8") as f:
                        f.write(content)
                    return output_filename
                return ""
            except Exception as e:
                message = str(e)
                # Handle rate limiting with exponential backoff
                if "Rate Limit Exceeded" in message or "429" in message:
                    wait_seconds = 30 * (attempt_index + 1)
                    print(f"Rate limit when scraping {url}. Retrying in {wait_seconds}s...")
                    await asyncio.sleep(wait_seconds)
                    continue
                print(f"Error scraping {url} with Firecrawl: {e}")
                return ""
        return ""

    async def scrape_all_sources_for_symbol(self, symbol: str) -> List[str]:
        """
        Orchestrates scraping for a single stock symbol from all defined sources.

        Returns:
            A list of file paths to the successfully scraped and saved data.
        """
        print(f"Starting scrape for symbol: {symbol}")
        successful_files: List[str] = []

        # 1. Scrape PSX first
        psx_file = await self._scrape_psx(symbol)
        if psx_file:
            successful_files.append(psx_file)

        # 2. Scrape StockAnalysis.com URLs with Firecrawl sequentially to avoid rate limits
        urls_to_scrape = self._get_stockanalysis_urls(symbol)
        for key, url in urls_to_scrape.items():
            output_path = os.path.join(self.session_dir, f"{symbol.upper()}_stockanalysis_{key}.md")
            result_path = await self._scrape_single_url_with_firecrawl(url, output_path)
            if result_path:
                successful_files.append(result_path)
            # small delay between calls as a courtesy and to avoid bursts
            await asyncio.sleep(1)

        print(f"Finished scrape for {symbol}. Saved {len(successful_files)} files.")
        return successful_files

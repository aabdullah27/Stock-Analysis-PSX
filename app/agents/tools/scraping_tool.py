import requests
from typing import Dict, Union

class DPS_PSX_Scraping_Tool:
    """
    A tool dedicated to scraping HTML content from the Pakistan Stock Exchange (PSX) data portal for a specific company symbol.
    """
    BASE_URL = "https://dps.psx.com.pk/company/{symbol}"

    def get_company_html(self, symbol: str) -> Dict[str, str]:
        """
        Fetches the raw HTML page for a given stock symbol from the PSX website.

        Args:
            symbol: The stock symbol to look up (e.g., 'BOP', 'OGDC').

        Returns:
            A dictionary containing the HTML content or an error message.
        """
        if not symbol or not isinstance(symbol, str):
            print("[tool] Invalid or empty symbol provided.")
            return {"error": "Invalid or empty symbol provided."}

        try:
            url = self.BASE_URL.format(symbol=symbol.upper())
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            print(f"[tool] Starting scraping for symbol {symbol.upper()} at {url}")
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

            # Return a structured dictionary with the symbol and its HTML content
            print(f"[tool] Successfully scraped {symbol.upper()} (status={response.status_code}, bytes={len(response.text)})")
            return {
                "symbol": symbol.upper(),
                "html_content": response.text
            }

        except requests.exceptions.HTTPError as http_err:
            print(f"[tool] HTTP error occurred for symbol {symbol}: {http_err}")
            return {"error": f"HTTP error occurred for symbol {symbol}: {http_err}"}
        except requests.exceptions.RequestException as req_err:
            print(f"[tool] Failed to retrieve data for symbol {symbol}: {req_err}")
            return {"error": f"Failed to retrieve data for symbol {symbol}: {req_err}"}
        except Exception as e:
            print(f"[tool] An unexpected error occurred for symbol {symbol}: {str(e)}")
            return {"error": f"An unexpected error occurred for symbol {symbol}: {str(e)}"}

# Expose the method as a simple function for the agent
psx_scraper = DPS_PSX_Scraping_Tool()

def scrape_psx_by_symbol(symbol: str) -> Dict[str, str]:
    """
    Tool function to fetch the HTML content for a stock symbol from dps.psx.com.pk.
    This provides real-time and fundamental data directly from the source.
    """
    return psx_scraper.get_company_html(symbol)
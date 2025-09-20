from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class ScrapeRequest(BaseModel):
    symbols: List[str] = Field(
        ...,
        max_length=5,
        example=["BOP", "OGDC"],
        description="A list of up to 5 PSX stock symbols to scrape."
    )

class ScrapeResponse(BaseModel):
    message: str
    session_id: str
    scraped_files: Dict[str, List[str]]
    # seconds for scraping plus upload to Gemini
    duration_seconds: Optional[float] = None

class AnalyzeRequest(BaseModel):
    session_id: str = Field(..., description="The session ID from a successful scraping request.")

class AnalyzeResponse(BaseModel):
    report: Optional[str] = None
    error: Optional[str] = None
    # seconds for analysis step only
    duration_seconds: Optional[float] = None
from pydantic import BaseModel, Field
from typing import List, Optional

class AnalysisRequest(BaseModel):
    symbols: List[str] = Field(
        ...,
        example=["BOP", "OGDC", "LUCK"],
        description="A list of 1 to 5 PSX stock symbols to analyze."
    )

class AnalysisResponse(BaseModel):
    report: Optional[str] = None
    error: Optional[str] = None

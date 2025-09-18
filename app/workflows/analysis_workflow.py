import logging
from typing import Dict, Any, List
from app.agents.research_agent import create_research_agent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnalysisWorkflow:
    """
    Orchestrates the analysis workflow by invoking the research agent.
    """
    def __init__(self):
        self.research_agent = create_research_agent()
        logger.info("AnalysisWorkflow initialized with Research Agent.")

    async def run_async(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Executes the analysis workflow for a list of stock symbols.

        Args:
            symbols: A list of stock symbols to analyze.

        Returns:
            A dictionary containing the final report or an error message.
        """
        if not symbols:
            return {"error": "No stock symbols provided for analysis."}

        # Create a single, clear prompt for the agent
        prompt = f"Please perform a fundamental analysis on the following PSX stock symbols: {', '.join(symbols)}"
        logger.info(f"Starting analysis for symbols: {', '.join(symbols)}")

        try:
            # Run the agent with the compiled prompt
            response = await self.research_agent.arun(prompt)

            if not response or not response.content:
                logger.error("Research agent returned an empty response.")
                return {"error": "Analysis failed to produce a result."}

            logger.info("Successfully generated analysis report.")
            return {"report": response.content}

        except Exception as e:
            logger.error(f"An error occurred during the analysis workflow: {e}", exc_info=True)
            return {"error": f"An unexpected error occurred: {str(e)}"}

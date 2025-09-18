from fastapi import APIRouter, HTTPException, status
from app.api.v1.schemas.analysis import AnalysisRequest, AnalysisResponse
from app.workflows.analysis_workflow import AnalysisWorkflow
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post(
    "/stocks",
    response_model=AnalysisResponse,
    summary="Analyze a list of PSX stock symbols"
)
async def analyze_stocks(request: AnalysisRequest):
    """
    Triggers the multi-tool agent workflow to perform fundamental analysis on a list of stocks.
    """
    if not request.symbols:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The 'symbols' list cannot be empty."
        )

    if len(request.symbols) > 10: # Limiting to 10 for performance
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Too many symbols. Please provide a maximum of 10 symbols per request."
        )

    try:
        logger.info(f"Received analysis request for symbols: {request.symbols}")
        workflow = AnalysisWorkflow()
        result = await workflow.run_async(request.symbols)

        if "error" in result:
            logger.error(f"Workflow failed with error: {result['error']}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )

        return AnalysisResponse(report=result.get("report"))

    except Exception as e:
        logger.error(f"An unexpected exception occurred in the endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

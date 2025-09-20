import os
import uuid
import shutil
from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from app.api.v1.schemas.analysis import ScrapeRequest, ScrapeResponse, AnalyzeRequest, AnalyzeResponse
from app.services.scraping_service import ScrapingService
from app.services.analysis_service import AnalysisService
from app.core.config import settings
import logging
import time

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory store mapping session_id -> list of gemini file names
SESSION_GEMINI_FILES = {}


def cleanup_session_folder(session_id: str):
    """Background task to remove a session's data folder."""
    session_path = os.path.join(settings.SCRAPING_OUTPUT_DIR, session_id)
    if os.path.isdir(session_path):
        try:
            shutil.rmtree(session_path)
            logger.info(f"Successfully cleaned up session folder: {session_path}")
        except Exception as e:
            logger.error(f"Error cleaning up session folder {session_path}: {e}")

@router.post(
    "/scrape",
    response_model=ScrapeResponse,
    summary="Step 1: Scrape data for given stock symbols"
)
async def scrape_data_for_symbols(request: ScrapeRequest):
    """
    Initiates the data gathering process. It scrapes all required web sources
    for each symbol and stores the data in a temporary session folder.
    Returns a session_id to be used for the analysis step.
    Also uploads the scraped files to Gemini to save time in the next step.
    """
    session_id = str(uuid.uuid4())
    logger.info(f"Starting scrape job with new session_id: {session_id}")
    scraping_service = ScrapingService(session_id)
    analysis_service = AnalysisService()

    start_time = time.time()
    scraped_files_map = {}
    try:
        # Scrape sequentially per symbol
        for symbol in request.symbols:
            files = await scraping_service.scrape_all_sources_for_symbol(symbol)
            scraped_files_map[symbol] = [os.path.basename(f) for f in files]

        # Gather all file paths for the session
        session_path = os.path.join(settings.SCRAPING_OUTPUT_DIR, session_id)
        file_paths = [os.path.join(session_path, f) for f in os.listdir(session_path)]

        # Upload to Gemini immediately and store remote names for later analyze step
        uploaded_names = analysis_service.upload_files_to_gemini(file_paths)
        SESSION_GEMINI_FILES[session_id] = uploaded_names

        duration_seconds = round(time.time() - start_time, 2)
        logger.info(f"Scrape+Upload completed in {duration_seconds}s for session {session_id}")
        print(f"Scrape+Upload duration: {duration_seconds}s (session {session_id})")

        return ScrapeResponse(
            message=f"Data scraping completed successfully in {duration_seconds}s. You can now proceed to the analysis step.",
            session_id=session_id,
            scraped_files=scraped_files_map,
            duration_seconds=duration_seconds
        )
    except Exception as e:
        logger.error(f"Scraping failed for session {session_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during scraping: {str(e)}"
        )

@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    summary="Step 2: Analyze scraped data from a session"
)
async def analyze_scraped_data(request: AnalyzeRequest, background_tasks: BackgroundTasks):
    """
    Uses the Gemini-uploaded files from the scrape step to generate the final analysis.
    Only deletes the Gemini files after completion; local files/folders are preserved.
    """
    session_path = os.path.join(settings.SCRAPING_OUTPUT_DIR, request.session_id)
    if not os.path.isdir(session_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session ID not found. Please initiate a new scrape request."
        )

    logger.info(f"Starting analysis for session {request.session_id}.")

    try:
        analysis_service = AnalysisService()
        uploaded_names = SESSION_GEMINI_FILES.get(request.session_id, [])
        if not uploaded_names:
            logger.warning("No Gemini files recorded for session; attempting on-the-fly upload.")
            file_paths = [os.path.join(session_path, f) for f in os.listdir(session_path)]
            uploaded_names = analysis_service.upload_files_to_gemini(file_paths)
            SESSION_GEMINI_FILES[request.session_id] = uploaded_names

        start_time = time.time()
        report = analysis_service.generate_report_from_gemini_files(uploaded_names)
        duration_seconds = round(time.time() - start_time, 2)
        logger.info(f"Analysis completed in {duration_seconds}s for session {request.session_id}")
        print(f"Analysis duration: {duration_seconds}s (session {request.session_id})")

        # Clean up Gemini files only
        analysis_service.delete_gemini_files(uploaded_names)
        SESSION_GEMINI_FILES.pop(request.session_id, None)

        if report.startswith("Error:"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=report
            )

        return AnalyzeResponse(report=report, duration_seconds=duration_seconds)

    except Exception as e:
        logger.error(f"Analysis failed for session {request.session_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during analysis: {str(e)}"
        )
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.core.config import settings
from app.api.v1 import api_router_v1
import os

# Load environment variables from .env file
load_dotenv()

# Ensure the root scraping directory exists
os.makedirs(settings.SCRAPING_OUTPUT_DIR, exist_ok=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="An API for a decoupled, two-step stock analysis system."
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.get("/")
async def root():
    return {"message": f"Welcome to the {settings.PROJECT_NAME} API"}

# Include the API router
app.include_router(api_router_v1, prefix=settings.API_V1_STR)

from fastapi import APIRouter
from app.api.v1.endpoints import analysis

api_router_v1 = APIRouter()
api_router_v1.include_router(analysis.router, prefix="/analysis", tags=["Stock Analysis Workflow"])
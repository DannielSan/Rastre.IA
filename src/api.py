from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import logging
import asyncio
import sys

# FIX: Force ProactorEventLoop on Windows for Playwright compatibility
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from src.pipeline import run_lead_pipeline

# Logging Setup
logger = logging.getLogger("api")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="LeadScraper API", version="1.0.0")

# CORS Configuration
# Allowing all origins for development/extension usage.
# specific extension ID can be added later for tighter security.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScrapeRequest(BaseModel):
    domain: str
    name: Optional[str] = None

class LeadResult(BaseModel):
    email: str
    domain: str
    status: str
    verification: dict
    found_at: str

@app.post("/api/scrape", response_model=List[LeadResult])
async def scrape_domain(request: ScrapeRequest):
    """
    Endpoint to scrape and verify leads for a specific domain.
    """
    logger.info(f"Received scrape request for: {request.domain}")
    try:
        results = await run_lead_pipeline(request.domain, request.name)
        if not results:
             return []
        return results
    except Exception as e:
        logger.error(f"Error processing {request.domain}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"message": "LeadScraper API is running. Go to /docs for the interface."}

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "LeadScraper API"}

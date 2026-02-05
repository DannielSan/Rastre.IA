import sys
import asyncio
import uvicorn

# WIN32 FIX: Force ProactorEventLoopPolicy for Playwright compatibility
# This must run BEFORE any asyncio loop is created.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

if __name__ == "__main__":
    # We run Uvicorn programmatically. 
    # Note: 'reload=True' might reset the policy in workers depending on how they spawn.
    # If this fails with reload, we will try with reload=False.
    print("--- Starting LeadScraper API with Windows Fix ---")
    uvicorn.run("src.api:app", host="127.0.0.1", port=8000, reload=True)

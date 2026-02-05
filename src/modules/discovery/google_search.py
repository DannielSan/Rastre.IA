import asyncio
import logging
import random
import urllib.parse
from typing import Set, List
from playwright.async_api import async_playwright

from src.modules.enrichment.extractor import extract_emails_from_text
from src.modules.verification.syntax import validate_email_syntax

logger = logging.getLogger(__name__)

class GoogleSearcher:
    def __init__(self, headless: bool = True):
        self.headless = headless

    async def _human_type(self, page, selector: str, text: str):
        """Simulates human typing with random delays."""
        await page.focus(selector)
        for char in text:
            await page.keyboard.type(char)
            await asyncio.sleep(random.uniform(0.05, 0.2)) # Random typing speed

    async def search(self, queries: List[str], max_results: int = 15) -> Set[str]:
        """
        Performs Google searches for the given queries and extracts emails.
        
        Args:
            queries (List[str]): List of search queries (Dorks).
            max_results (int): Approximate max results to process per query.
            
        Returns:
            Set[str]: Unique found emails.
        """
        found_emails = set()
        
        async with async_playwright() as p:
            # Launch with a persistent-looking context to be less suspicious
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 720},
                locale="en-US"
            )
            
            page = await context.new_page()
            
            # Go to Google once
            try:
                await page.goto("https://www.google.com", timeout=15000)
                await asyncio.sleep(random.uniform(1, 3))
            except Exception as e:
                logger.error(f"Failed to load Google: {e}")
                await browser.close()
                return found_emails

            for query in queries:
                try:
                    logger.info(f"Executing Google Dork: {query}")
                    
                    # Type query into the search box
                    search_box = page.locator('textarea[name="q"]').first
                    if not await search_box.is_visible():
                         # Fallback for some regions/versions
                         search_box = page.locator('input[name="q"]').first
                         
                    await search_box.clear()
                    await self._human_type(page, 'textarea[name="q"]', query)
                    await asyncio.sleep(random.uniform(0.5, 1.0))
                    await page.keyboard.press("Enter")
                    
                    # Wait for results
                    await page.wait_for_selector('#search', timeout=10000)
                    await asyncio.sleep(random.uniform(2, 4)) # Read results like a human
                    
                    # Extract content from the results container
                    content = await page.inner_text('#search')
                    
                    # Extract emails
                    emails = extract_emails_from_text(content)
                    
                    # Clean and validate
                    valid_for_query = 0
                    for email in emails:
                        # Extra cleanup for google formatting (e.g. 'user@domain.com...' -> 'user@domain.com')
                        clean_email = email.rstrip('.,:;')
                        if validate_email_syntax(clean_email):
                            found_emails.add(clean_email)
                            valid_for_query += 1
                            
                    logger.info(f"Found {valid_for_query} potential emails for query: {query}")
                    
                    # Random sleep between queries
                    await asyncio.sleep(random.uniform(3, 7))
                    
                except Exception as e:
                    logger.error(f"Error during search '{query}': {str(e)}")
                    continue
            
            await browser.close()
            
        return found_emails

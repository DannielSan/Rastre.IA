import asyncio
import logging
from typing import List, Set
from playwright.async_api import async_playwright, Page, BrowserContext

from src.modules.enrichment.extractor import extract_emails_from_text
from src.modules.verification.syntax import validate_email_syntax

logger = logging.getLogger(__name__)

class DomainScraper:
    def __init__(self, headless: bool = True):
        self.headless = headless
        
    async def scrape_domain(self, domain: str, max_pages: int = 5) -> Set[str]:
        """
        Scrapes a domain for email addresses, visiting common pages.
        
        Args:
            domain (str): The domain to scrape (e.g., 'example.com').
            max_pages (int): Maximum number of pages to visit.
            
        Returns:
            Set[str]: A set of unique, syntax-valid emails found.
        """
        # Ensure protocol
        if not domain.startswith("http"):
            base_url = f"https://{domain}"
        else:
            base_url = domain
            
        found_emails = set()
        visited_urls = set()
        
        # Common paths to check
        paths_to_check = ["/", "/contact", "/about", "/team", "/contato", "/sobre", "/equipe"]
        urls_to_visit = [f"{base_url.rstrip('/')}{path}" for path in paths_to_check]
        
        async with async_playwright() as p:
            # Optimize: Disable images and unnecessary resources
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
            
            # Block resources for performance
            await context.route("**/*", lambda route: route.abort() 
                if route.request.resource_type in ["image", "media", "stylesheet", "font"] 
                else route.continue_()
            )
            
            page = await context.new_page()
            
            for url in urls_to_visit:
                if len(visited_urls) >= max_pages:
                    break
                
                try:
                    logger.info(f"Visiting {url}...")
                    # Fast timeout, don't wait mainly for network idle if it's too slow
                    response = await page.goto(url, timeout=10000, wait_until="domcontentloaded")
                    
                    if not response or response.status >= 400:
                        logger.warning(f"Failed to load {url} (Status: {response.status if response else 'Unknown'})")
                        continue
                        
                    content = await page.content()
                    
                    # Extract emails from visible text and mailto links
                    # 1. Regex on full content
                    raw_emails = extract_emails_from_text(content)
                    
                    # 2. Check for mailto links specifically (sometimes obfuscated in text but clear in href)
                    mailto_links = await page.evaluate("""() => {
                        const links = Array.from(document.querySelectorAll('a[href^="mailto:"]'));
                        return links.map(link => link.href.replace('mailto:', '').split('?')[0]);
                    }""")
                    raw_emails.update(mailto_links)
                    
                    # Filter valid emails
                    for email in raw_emails:
                        if validate_email_syntax(email):
                            found_emails.add(email)
                            
                    visited_urls.add(url)
                    
                except Exception as e:
                    logger.error(f"Error scraping {url}: {str(e)}")
                    continue
            
            await browser.close()
            
        return found_emails

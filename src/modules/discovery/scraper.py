import asyncio
import logging
from typing import List, Set
from playwright.async_api import async_playwright, Page, BrowserContext

from src.modules.enrichment.extractor import extract_emails_from_text
from src.modules.verification.syntax import validate_email_syntax
from src.utils.browser import browser_utils

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
            
            # Use safe context with randomized UA/Proxy
            context = await browser_utils.new_safe_context(browser)
            
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
                    # Wait for network idle to ensure SPAs are loaded
                    response = None
                    try:
                        response = await page.goto(url, timeout=15000, wait_until="domcontentloaded")
                        await page.wait_for_load_state("networkidle", timeout=5000)
                    except Exception:
                        pass # Continue even if networkidle times out
                    
                    if not response or response.status >= 400:
                        logger.warning(f"Failed to load {url} (Status: {response.status if response else 'Unknown'})")
                        continue
                        
                    content = await page.content()
                    
                    # 1. Regex on full HTML content
                    raw_emails = extract_emails_from_text(content)
                    
                    # 2. Advanced DOM Extraction (JS Execution)
                    # Extracts from: mailto links, generic hrefs, and visible text nodes
                    dom_emails = await page.evaluate("""() => {
                        const emails = new Set();
                        const emailRegex = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}/g;
                        
                        // 1. Scan all 'href' attributes
                        document.querySelectorAll('*[href]').forEach(el => {
                            const href = el.getAttribute('href');
                            if (href && href.includes('mailto:')) {
                                emails.add(href.replace('mailto:', '').split('?')[0]);
                            } else if (href && href.match(emailRegex)) {
                                const match = href.match(emailRegex);
                                if (match) match.forEach(e => emails.add(e));
                            }
                        });

                        // 2. Scan visible text
                        const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null, false);
                        let node;
                        while (node = walker.nextNode()) {
                            if (node.parentElement && node.parentElement.offsetParent !== null) { // Check visibility
                                const matches = node.nodeValue.match(emailRegex);
                                if (matches) matches.forEach(e => emails.add(e));
                            }
                        }
                        
                        return Array.from(emails);
                    }""")
                    raw_emails.update(dom_emails)
                    
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

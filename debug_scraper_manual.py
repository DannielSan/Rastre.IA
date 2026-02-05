import asyncio
import logging
from src.modules.discovery.scraper import DomainScraper
from src.utils.browser import browser_utils

# Setup logging to see what's happening
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("debug_scraper")

async def debug_domain(domain: str):
    print(f"--- Debugging {domain} ---")
    
    # 1. Initialize Scraper with Headless=FALSE to see the browser
    scraper = DomainScraper(headless=False) 
    
    print("Launching browser...")
    emails = await scraper.scrape_domain(domain, max_pages=1)
    
    print("\n--- Results ---")
    print(f"Found {len(emails)} emails:")
    for email in emails:
        print(f" - {email}")
        
    if not emails:
        print("NO EMAILS FOUND. Saving HTML dump for inspection...")
        content = await scraper.page.content() # We need to access the page object
        with open("debug_dump.html", "w", encoding="utf-8") as f:
            f.write(content)
        print("Saved 'debug_dump.html'.")
        
    print("Reasons might include: dynamic loading, iframes, or obfuscation.")

# Modified Scraper access for debugging
# We need to monkey-patch or adjust the script to access the 'page' object
# or just run raw playwright here for simplicity
async def raw_debug(domain):
    print(f"--- Raw Debugging {domain} ---")
    from playwright.async_api import async_playwright
    
    from src.utils.browser import browser_utils # Import
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # page = await browser.new_page() # OLD
        context = await browser_utils.new_safe_context(browser) # NEW
        
        # Block resources for performance (LIKE SCRAPER.PY)
        await context.route("**/*", lambda route: route.abort() 
            if route.request.resource_type in ["image", "media", "stylesheet", "font"] 
            else route.continue_()
        )
        
        page = await context.new_page()
        try:
            await page.goto(f"https://{domain}", timeout=30000, wait_until="domcontentloaded")
            
            # 1. Dump content
            content = await page.content()
            with open("debug_dump.html", "w", encoding="utf-8") as f:
                f.write(content)
            print("Saved debug_dump.html")
            
            # 2. Try to find mailto
            mailtos = await page.evaluate("() => Array.from(document.querySelectorAll('a[href^=\"mailto:\"]')).map(a => a.href)")
            print(f"Mailtos found: {mailtos}")
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(raw_debug("opentreinamentos.com.br"))

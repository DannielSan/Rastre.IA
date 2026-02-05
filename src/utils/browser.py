import random
import logging
from typing import Optional, Dict
from fake_useragent import UserAgent
from playwright.async_api import Browser, BrowserContext

from src.config.settings import settings

logger = logging.getLogger(__name__)

class BrowserUtils:
    def __init__(self):
        self.ua = UserAgent()
        
    def get_random_user_agent(self) -> str:
        """Returns a random User-Agent string."""
        try:
            return self.ua.random
        except Exception:
            # Fallback if fake-useragent fails
            return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    def get_random_proxy(self) -> Optional[Dict[str, str]]:
        """
        Returns a random proxy configuration if proxies are defined in settings.
        Format: {'server': 'http://user:pass@host:port'}
        """
        if not settings.PROXIES:
            return None
            
        proxy_url = random.choice(settings.PROXIES)
        return {"server": proxy_url}

    async def new_safe_context(self, browser: Browser, **kwargs) -> BrowserContext:
        """
        Creates a new browser context with randomized Anti-Fingerprinting settings.
        """
        user_agent = self.get_random_user_agent()
        proxy = self.get_random_proxy()
        
        logger.debug(f"Creating context with UA: {user_agent[:30]}... Proxy: {proxy}")
        
        context = await browser.new_context(
            user_agent=user_agent,
            proxy=proxy,
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
            timezone_id="America/New_York",
            **kwargs
        )
        
        # Additional evasion: Disable webdriver flag
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        return context

browser_utils = BrowserUtils()

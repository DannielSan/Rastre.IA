import dns.asyncresolver
import dns.exception
import logging
from src.config.settings import settings
from src.core.exceptions import DNSLookupError, ValidationTimeoutError

logger = logging.getLogger(__name__)

async def check_mx_record(domain: str) -> bool:
    """
    Asynchronously checks if a domain has valid MX records.
    
    Args:
        domain (str): The domain to check.
        
    Returns:
        bool: True if MX records exist, False otherwise.
    """
    resolver = dns.asyncresolver.Resolver()
    resolver.timeout = settings.DNS_TIMEOUT
    resolver.lifetime = settings.DNS_TIMEOUT

    try:
        # Query MX records
        answers = await resolver.resolve(domain, 'MX')
        return len(answers) > 0
        
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
        # Domain exists but no MX validation, or Domain does not exist
        return False
        
    except dns.exception.Timeout:
        logger.warning(f"DNS timeout for domain: {domain}")
        # In a strict scraping context, timeout usually means we can't verify, so treated as invalid or 'unknown'
        # For this boolean check, we'll return False but log it.
        return False
        
    except Exception as e:
        logger.error(f"DNS lookup error for {domain}: {str(e)}")
        return False

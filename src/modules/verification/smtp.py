import asyncio
import smtplib
import logging
import random
import string
import dns.asyncresolver
from typing import Optional, Tuple

from src.config.settings import settings

logger = logging.getLogger(__name__)

async def get_mx_record(domain: str) -> Optional[str]:
    """Resolves the highest priority MX record for a domain."""
    try:
        resolver = dns.asyncresolver.Resolver()
        resolver.timeout = settings.DNS_TIMEOUT
        resolver.lifetime = settings.DNS_TIMEOUT
        answers = await resolver.resolve(domain, 'MX')
        # Sort by preference (lowest first)
        sorted_answers = sorted(answers, key=lambda r: r.preference)
        return str(sorted_answers[0].exchange).rstrip('.')
    except Exception:
        return None

def verify_smtp_sync(email: str, mx_host: str, timeout: int = 10) -> Tuple[bool, str]:
    """
    Synchronous SMTP check to be run in executor.
    Returns (is_valid, message).
    """
    try:
        # 1. Connect
        server = smtplib.SMTP(mx_host, 25, timeout=timeout)
        server.ehlo_or_helo_if_needed()
        
        # 2. Mail From (use a fake but valid-looking source)
        server.mail('verify@leadscraper-check.com')
        
        # 3. Rcpt To
        code, message = server.rcpt(email)
        server.quit()
        
        # 250 = OK, 251 = User not local; will forward
        if code == 250 or code == 251:
            return True, "OK"
        else:
            return False, f"Server returned {code}"
            
    except smtplib.SMTPConnectError:
        return False, "Connection Failed"
    except smtplib.SMTPServerDisconnected:
        return False, "Server Disconnected"
    except Exception as e:
        return False, f"Error: {str(e)}"

async def verify_email_smtp(email: str) -> str:
    """
    Verifies an email using SMTP.
    Returns: 'valid', 'invalid', 'catch_all', 'unknown'
    """
    domain = email.split('@')[-1]
    mx_host = await get_mx_record(domain)
    
    if not mx_host:
        return "unknown" # No MX, can't verify SMTP
        
    loop = asyncio.get_running_loop()
    
    # 1. Catch-All Check
    # Generate a random impossible email to test if server accepts everything
    random_prefix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=15))
    validation_email = f"{random_prefix}@{domain}"
    
    is_valid_catch_all, msg = await loop.run_in_executor(
        None, verify_smtp_sync, validation_email, mx_host, settings.SMTP_TIMEOUT
    )
    
    if is_valid_catch_all:
        logger.info(f"Domain {domain} is Catch-All (Accepted {validation_email})")
        return "catch_all"
        
    # 2. Verify Target Email
    is_valid, msg = await loop.run_in_executor(
        None, verify_smtp_sync, email, mx_host, settings.SMTP_TIMEOUT
    )
    
    if is_valid:
        return "valid"
    elif "Connection Failed" in msg or "timeout" in msg.lower():
        # Distinguish between "User Unknown" (False) and "Can't Connect" (Unknown)
        return "unknown"
    else:
        return "invalid"

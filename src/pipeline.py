import asyncio
import logging
from typing import List, Optional
from datetime import datetime

from src.modules.discovery.scraper import DomainScraper
from src.modules.discovery.google_search import GoogleSearcher
from src.modules.verification.syntax import extract_domain, validate_email_syntax
from src.modules.verification.mx import check_mx_record
from src.modules.verification.smtp import verify_email_smtp
from src.modules.enrichment.patterns import generate_common_aliases, generate_name_patterns

logger = logging.getLogger(__name__)

async def run_lead_pipeline(domain: str, input_name: str = None) -> List[dict]:
    """
    Runs the full lead generation pipeline for a single domain.
    Returns a list of lead dictionaries.
    """
    logger.info(f"Starting pipeline for domain: {domain}")
    found_emails = set()
    
    try:
        # 1. Direct Scrape
        scraper = DomainScraper()
        scraped_emails = await scraper.scrape_domain(domain)
        found_emails.update(scraped_emails)
        
        # 2. Google Search (Dorking)
        logger.info("Starting Google Search (Dorking)...")
        google_searcher = GoogleSearcher()
        dorks = [
            f'site:linkedin.com "{domain}" "email"',
            f'site:{domain} "email"',
            f'"{domain}" "contact" email'
        ]
        google_emails = await google_searcher.search(dorks)
        found_emails.update(google_emails)
        
        logger.info(f"Total found via Scraping + Google: {len(found_emails)}")

        # 3. Predict (Enrichment)
        predicted_emails = []
        if input_name:
            logger.info(f"Generating patterns for name: {input_name}")
            predicted_emails.extend(generate_name_patterns(input_name, domain))
            
        predicted_emails.extend(generate_common_aliases(domain))
        
        for email in predicted_emails:
            if validate_email_syntax(email):
                found_emails.add(email)
                
        logger.info(f"Total candidates to verify: {len(found_emails)}")
        
        # 4. Verify
        results = []
        for email in found_emails:
            lead_data = {
                "email": email,
                "domain": domain,
                "found_at": datetime.utcnow().isoformat(),
                "status": "processing",
                "verification": {
                    "syntax": True, # Regex checked implicitly
                    "mx": False,
                    "smtp": "unchecked"
                }
            }
            
            # MX Check
            email_domain = extract_domain(email)
            if email_domain:
                mx_valid = await check_mx_record(email_domain)
                lead_data["verification"]["mx"] = mx_valid
                
                if mx_valid:
                    # SMTP Check
                    smtp_status = await verify_email_smtp(email)
                    lead_data["verification"]["smtp"] = smtp_status
                    
                    if smtp_status == "valid":
                        lead_data["status"] = "valid"
                    elif smtp_status == "catch_all":
                        lead_data["status"] = "catch_all"
                    elif smtp_status == "invalid":
                        lead_data["status"] = "invalid"
                    else:
                        lead_data["status"] = "risky"
                else:
                     lead_data["status"] = "invalid_mx"
            else:
                 lead_data["status"] = "invalid_format"
                
            results.append(lead_data)
            logger.info(f"Processed: {email} -> {lead_data['status']}")
            
        return results

    except Exception as e:
        logger.error(f"Pipeline failed for {domain}: {e}")
        return []

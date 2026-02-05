import asyncio
import json
import logging
import sys
import os
from datetime import datetime

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

from src.modules.discovery.scraper import DomainScraper
from src.modules.verification.syntax import extract_domain, validate_email_syntax
from src.modules.verification.mx import check_mx_record
from src.modules.verification.smtp import verify_email_smtp
from src.modules.enrichment.patterns import generate_common_aliases, generate_name_patterns

# Configure simple logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def process_domain(domain: str, input_name: str = None, output_file: str = "leads.json"):
    logger.info(f"Starting process for domain: {domain}")
    
    found_emails = set()
    
    # 1. Direct Scrape
    scraper = DomainScraper()
    scraped_emails = await scraper.scrape_domain(domain)
    found_emails.update(scraped_emails)
    
    # 2. Google Search (Dorking)
    from src.modules.discovery.google_search import GoogleSearcher
    
    logger.info("Starting Google Search (Dorking)...")
    google_searcher = GoogleSearcher()
    dorks = [
        f'site:linkedin.com "{domain}" "email"',
        f'site:{domain} "email"',
        f'"{domain}" "contact" email'
    ]
    google_emails = await google_searcher.search(dorks)
    found_emails.update(google_emails)
    
    target_emails_count = len(found_emails)
    logger.info(f"Total found via Scraping + Google: {target_emails_count}")

    # 3. Predict (Enrichment)
    # Only if we have very fews results or explicitly requested, 
    # but for this tool we always want to try predicting common aliases.
    predicted_emails = []
    
    if input_name:
        logger.info(f"Generating patterns for name: {input_name}")
        predicted_emails.extend(generate_name_patterns(input_name, domain))
        
    # Add common aliases regardless (optional, but good for "LeadScraper")
    predicted_emails.extend(generate_common_aliases(domain))
    
    # Verify predictions are syntactically valid (just in case)
    for email in predicted_emails:
        if validate_email_syntax(email):
            found_emails.add(email)
            
    logger.info(f"Total candidates to verify: {len(found_emails)}")
    
    results = []
    
    # 3. Verify
    for email in found_emails:
        lead_data = {
            "email": email,
            "source_domain": domain,
            "found_at": datetime.utcnow().isoformat(),
            "status": "processing",
            "verification": {
                "syntax": True,
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
                
                # Final Status Determination
                if smtp_status == "valid":
                    lead_data["status"] = "valid"
                elif smtp_status == "catch_all":
                    lead_data["status"] = "catch_all"
                elif smtp_status == "invalid":
                    lead_data["status"] = "invalid"
                else: # unknown
                    lead_data["status"] = "risky"
            else:
                 lead_data["status"] = "invalid_mx"
        else:
             lead_data["status"] = "invalid_format"
            
        results.append(lead_data)
        logger.info(f"Processed: {email} -> {lead_data['status']} (SMTP: {lead_data['verification']['smtp']})")

    # 4. Save
    try:
        existing_data = []
        if os.path.exists(output_file):
            with open(output_file, "r") as f:
                try:
                    existing_data = json.load(f)
                except json.JSONDecodeError:
                    pass
        
        # Deduplicate based on email
        existing_map = {item['email']: item for item in existing_data}
        for res in results:
            existing_map[res['email']] = res # Update/Overwrite
            
        final_data = list(existing_map.values())
        
        with open(output_file, "w") as f:
            json.dump(final_data, f, indent=2)
            
        logger.info(f"Saved {len(final_data)} unique leads to {output_file}")
        
    except Exception as e:
        logger.error(f"Failed to save results: {e}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Scrape and Verify Emails")
    parser.add_argument("domain", help="Target domain")
    parser.add_argument("--name", help="Person name for pattern prediction", default=None)
    
    args = parser.parse_args()
    
    asyncio.run(process_domain(args.domain, args.name))

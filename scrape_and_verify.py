import asyncio
import json
import logging
import sys
import os
from datetime import datetime

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

from src.modules.discovery.scraper import DomainScraper
from src.modules.verification.mx import check_mx_record
from src.modules.verification.syntax import extract_domain

# Configure simple logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def process_domain(domain: str, output_file: str = "leads.json"):
    logger.info(f"Starting process for domain: {domain}")
    
    # 1. Scrape
    scraper = DomainScraper()
    emails = await scraper.scrape_domain(domain)
    
    if not emails:
        logger.warning("No emails found via scraping.")
        return
        
    logger.info(f"Found {len(emails)} potential emails. Starting verification...")
    
    results = []
    
    # 2. Verify
    for email in emails:
        lead_data = {
            "email": email,
            "source_domain": domain,
            "found_at": datetime.utcnow().isoformat(),
            "status": "unknown",
            "mx_valid": False
        }
        
        email_domain = extract_domain(email)
        if email_domain:
            # Check MX
            mx_valid = await check_mx_record(email_domain)
            lead_data["mx_valid"] = mx_valid
            
            if mx_valid:
                lead_data["status"] = "verified_mx"
            else:
                lead_data["status"] = "invalid_mx"
        else:
            lead_data["status"] = "invalid_format"
            
        results.append(lead_data)
        print(f"Processed: {email} -> {lead_data['status']}")

    # 3. Save
    try:
        # Read existing data if possible to append
        existing_data = []
        if os.path.exists(output_file):
            with open(output_file, "r") as f:
                try:
                    existing_data = json.load(f)
                except json.JSONDecodeError:
                    pass
        
        existing_data.extend(results)
        
        with open(output_file, "w") as f:
            json.dump(existing_data, f, indent=2)
            
        logger.info(f"Saved {len(results)} leads to {output_file}")
        
    except Exception as e:
        logger.error(f"Failed to save results: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scrape_and_verify.py <domain>")
        sys.exit(1)
        
    target_domain = sys.argv[1]
    asyncio.run(process_domain(target_domain))

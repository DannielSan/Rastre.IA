import pandas as pd
import logging
from typing import List, Any
import os

logger = logging.getLogger(__name__)

def flatten_lead_data(data: List[dict]) -> List[dict]:
    """Flattens nested JSON structure for CSV/Excel export."""
    flat_data = []
    for item in data:
        # Basic fields
        flat_item = {
            "email": item.get("email"),
            "domain": item.get("source_domain"),
            "status": item.get("status"),
            "found_at": item.get("found_at"),
            # Verification details
            "valid_syntax": item.get("verification", {}).get("syntax"),
            "valid_mx": item.get("verification", {}).get("mx"),
            "valid_smtp": item.get("verification", {}).get("smtp"),
        }
        flat_data.append(flat_item)
    return flat_data

def export_to_csv(data: List[dict], filename: str = "leads.csv"):
    """Exports data to CSV."""
    if not data:
        logger.warning("No data to export.")
        return
        
    try:
        flat_data = flatten_lead_data(data)
        df = pd.DataFrame(flat_data)
        df.to_csv(filename, index=False)
        logger.info(f"Exported {len(data)} rows to {filename}")
    except Exception as e:
        logger.error(f"Failed to export CSV: {e}")

def export_to_excel(data: List[dict], filename: str = "leads.xlsx"):
    """Exports data to Excel."""
    if not data:
        logger.warning("No data to export.")
        return
        
    try:
        flat_data = flatten_lead_data(data)
        df = pd.DataFrame(flat_data)
        df.to_excel(filename, index=False)
        logger.info(f"Exported {len(data)} rows to {filename}")
    except Exception as e:
        logger.error(f"Failed to export Excel: {e}")

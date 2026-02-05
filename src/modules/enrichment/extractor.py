import re
from typing import Set

# Reuse the regex from syntax module or define a broader one for extraction
# For extraction, a slightly looser regex is often better to catch edge cases, 
# then filter with the strict validator.
EMAIL_REGEX_EXTRACT = re.compile(
    r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
)

def extract_emails_from_text(text: str) -> Set[str]:
    """
    Extracts all potential email addresses from a given text.
    
    Args:
        text (str): The raw text to search.
        
    Returns:
        Set[str]: A set of unique potential email addresses found.
    """
    if not text:
        return set()
        
    found = set(EMAIL_REGEX_EXTRACT.findall(text))
    # Basic cleanup: remove trailing dots/punctuation that might be captured
    cleaned = {e.rstrip('.,;:)]}') for e in found}
    return cleaned

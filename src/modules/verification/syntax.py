import re
from typing import Optional

# General Email Regex (RFC 5322 Official Standard compliant variant)
# We use a slightly simplified version often used in production for practicality
EMAIL_REGEX = re.compile(
    r"(^[-!#$%&'*+/=?^_`{}|~0-9a-zA-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9a-zA-Z]+)*"  # dot-atom
    r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-011\013\014\016-\177])*"'  # quoted-string
    r')@(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,63}$'  # domain
)

def validate_email_syntax(email: str) -> bool:
    """
    Validates the syntax of an email address using Regex.
    
    Args:
        email (str): The email address to validate.
        
    Returns:
        bool: True if syntax is valid, False otherwise.
    """
    if not email or not isinstance(email, str):
        return False
        
    if len(email) > 254:
        return False
        
    return bool(EMAIL_REGEX.match(email))

def extract_domain(email: str) -> Optional[str]:
    """
    Extracts the domain part from an email address.
    
    Args:
        email (str): The email address.
        
    Returns:
        str | None: The domain if found, else None.
    """
    try:
        return email.split('@')[1]
    except IndexError:
        return None

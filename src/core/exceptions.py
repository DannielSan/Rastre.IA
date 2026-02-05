class LeadScraperException(Exception):
    """Base exception for LeadScraper"""
    pass

class VerificationException(LeadScraperException):
    """Base exception for verification errors"""
    pass

class DNSLookupError(VerificationException):
    """Raised when DNS lookup fails"""
    pass

class ValidationTimeoutError(VerificationException):
    """Raised when validation times out"""
    pass

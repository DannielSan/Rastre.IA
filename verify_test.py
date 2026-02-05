import asyncio
import sys
import os

# Add src to path so we can import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

from src.modules.verification.syntax import validate_email_syntax, extract_domain
from src.modules.verification.mx import check_mx_record

async def test_email(email: str):
    print(f"\n--- Testing: {email} ---")
    
    # 1. Syntax Check
    is_valid_syntax = validate_email_syntax(email)
    print(f"Syntax Valid: {is_valid_syntax}")
    
    if not is_valid_syntax:
        print("Skipping MX check due to invalid syntax.")
        return

    # 2. Extract Domain
    domain = extract_domain(email)
    print(f"Domain: {domain}")
    
    # 3. MX Check
    if domain:
        has_mx = await check_mx_record(domain)
        print(f"MX Records Found: {has_mx}")
    else:
        print("Could not extract domain.")

async def main():
    test_emails = [
        "test@gmail.com",           # Valid
        "contact@google.com",       # Valid
        "invalid-email@",           # Invalid Syntax
        "user@nonexistent-domain-123xyz.com", # Valid Syntax, No MX
        "user@example.com"          # Valid Syntax, likely MX (IANA reserved)
    ]
    
    print("Starting Verification Tests...")
    for email in test_emails:
        await test_email(email)
    print("\nTests Completed.")

if __name__ == "__main__":
    asyncio.run(main())

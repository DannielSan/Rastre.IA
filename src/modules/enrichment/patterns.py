from typing import List
from unidecode import unidecode

def clean_name(name: str) -> str:
    """Removes accents and converts to lowercase."""
    return unidecode(name).lower().strip()

def generate_common_aliases(domain: str) -> List[str]:
    """Generates emails with common role-based aliases."""
    aliases = [
        "contact", "info", "admin", "sales", "support", "hello", "marketing", 
        "team", "hr", "carreiras", "vendas", "contato", "comercial"
    ]
    return [f"{alias}@{domain}" for alias in aliases]

def generate_name_patterns(full_name: str, domain: str) -> List[str]:
    """
    Generates email patterns based on a person's name.
    Example: "João Silva" -> joao@, joao.silva@, jsilva@, etc.
    """
    if not full_name:
        return []

    parts = clean_name(full_name).split()
    if len(parts) < 1:
        return []

    first = parts[0]
    last = parts[-1] if len(parts) > 1 else ""
    
    patterns = [
        f"{first}@{domain}", # joao@
    ]
    
    if last:
        patterns.extend([
            f"{first}.{last}@{domain}", # joao.silva@
            f"{first}{last}@{domain}",  # joaosilva@
            f"{first[0]}{last}@{domain}", # jsilva@
            f"{first}_{last}@{domain}", # joao_silva@
        ])
        
    return patterns

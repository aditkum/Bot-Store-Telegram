def format_currency(amount: int) -> str:
    """Format IDR currency"""
    return f"Rp{amount:,}".replace(",", ".")

def validate_phone(phone: str) -> bool:
    """Validate Indonesian phone number"""
    import re
    pattern = r"^\+62\d{9,12}$"
    return re.match(pattern, phone) is not None


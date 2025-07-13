   # File utils.py yang benar
def format_currency(amount):
       """Format angka ke format mata uang Indonesia"""
   return f"Rp{amount:,.0f}".replace(",", ".")

def validate_phone(number):
       """Validasi nomor telepon Indonesia"""
   import re
   return re.match(r"^\+62\d{9,12}$", number) is not None

   # Ekspor fungsi-fungsi
   utils = {
       'format_currency': format_currency,
       'validate_phone': validate_phone
   }
   

   # /root/Bot-Store-Telegram/bot/modules/utils.py
   def format_currency(amount):
       """Format angka ke dalam format mata uang IDR"""
       return f"Rp{amount:,.0f}".replace(",", ".")

   # Ekspor objek utama
   utils = {
       'format_currency': format_currency,
       # fungsi tambahan bisa ditambahkan di sini
   }
   

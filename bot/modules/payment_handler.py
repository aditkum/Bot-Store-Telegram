import requests
from dotenv import load_dotenv
import os

load_dotenv()
# /root/Bot-Store-Telegram/bot/modules/payment.py

class PaymentHandler:
    def create_payment(self, user_id, product_id, amount):
        # Logika untuk membuat pembayaran
        # Misalnya, menghubungi API pembayaran dan mengembalikan URL pembayaran
        try:
            payment_url = f"https://payment-gateway.example.com/pay?user_id={user_id}&amount={amount}"
            return {
                'payment_url': payment_url,
                'amount': amount
            }
        except Exception as e:
            return {'error': str(e)}

class PaymentGateway:
    def __init__(self):
        self.api_key = os.getenv("VIOLET_API_KEY")
        self.secret_key = os.getenv("VIOLET_SECRET_KEY")
    
    def create_transaction(self, amount):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "amount": amount,
            "currency": "IDR"
        }
        
        response = requests.post(
            "https://api.violetmediapay.com/transactions",
            headers=headers,
            json=payload
        )
        return response.json()

# Inisialisasi instance
payment_gateway = PaymentGateway()

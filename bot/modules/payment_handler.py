import requests
from dotenv import load_dotenv
import os

load_dotenv()

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

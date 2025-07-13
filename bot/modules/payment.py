import os
import hmac
import hashlib
import requests
from datetime import datetime

class PaymentHandler:
    def __init__(self):
        self.base_url = (
            "https://violetmediapay.com/api/live/"
            if os.getenv("PAYMENT_ENV") == "live" 
            else "https://violetmediapay.com/api/sandbox/"
        )
        self.headers = {
            "Authorization": f"Bearer {os.getenv('PAYMENT_API_KEY')}",
            "Content-Type": "application/json"
        }

    def _generate_signature(self, ref_id: str, amount: int) -> str:
        secret = os.getenv("PAYMENT_SECRET_KEY").encode()
        message = f"{ref_id}{os.getenv('PAYMENT_API_KEY')}{amount}".encode()
        return hmac.new(secret, message, hashlib.sha256).hexdigest()

    def create_payment(self, user_id: int, product_id: str, amount: int) -> dict:
        ref_id = f"VVIP-{datetime.now().strftime('%Y%m%d')}-{user_id}"
        payload = {
            "ref_id": ref_id,
            "amount": amount,
            "signature": self._generate_signature(ref_id, amount),
            "callback_url": f"{os.getenv('WEBHOOK_URL')}/callback"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}create",
                headers=self.headers,
                json=payload
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}


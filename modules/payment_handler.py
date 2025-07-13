import os
import logging
import requests
import hashlib
import hmac
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

# Inisialisasi logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Setup database
client = MongoClient(os.getenv("MONGO_URI"))
db = client['vvip_bot']
payments_col = db['payments']
transactions_col = db['transactions']

class PaymentHandler:
    """
    Mengelola semua proses pembayaran termasuk:
    - Membuat transaksi baru
    - Memverifikasi status transaksi
    - Menangani callback
    """

    def __init__(self):
        self.api_key = os.getenv("PAYMENT_API_KEY")
        self.secret_key = os.getenv("PAYMENT_SECRET_KEY")
        self.base_url = "https://violetmediapay.com/api/live/transactions"  # Ganti dengan live saat produksi

    def create_signature(self, ref_kode: str, amount: str) -> str:
        """Membuat signature untuk permintaan transaksi"""
        signature = hmac.new(
            self.secret_key.encode(),
            (ref_kode + self.api_key + amount).encode(),
            hashlib.sha256
        ).hexdigest()
        return signature

    def create_transaction(self, user_id: int, product_id: str, amount: int) -> dict:
        """Membuat transaksi baru"""
        try:
            ref_kode = f"VVIP-{datetime.now().strftime('%Y%m%d')}-{user_id}-{product_id}"
            signature = self.create_signature(ref_kode, str(amount))

            payload = {
                "ref_kode": ref_kode,
                "amount": amount,
                "signature": signature,
                "nama": "Nama Pelanggan",  # Ganti dengan nama pelanggan
                "email": "emailpelanggan@gmail.com",  # Ganti dengan email pelanggan
                "phone": "No Hanphone",  # Ganti dengan nomor telepon pelanggan
                "produk": product_id
            }

            response = requests.post(f"{self.base_url}/create", json=payload)

            if response.status_code == 200:
                data = response.json()
                if data['status']:
                    # Simpan data pembayaran
                    payments_col.insert_one({
                        "order_id": ref_kode,
                        "user_id": user_id,
                        "product_id": product_id,
                        "amount": amount,
                        "status": "pending",
                        "created_at": datetime.now(),
                        "checkout_url": data['data'][0]['checkout_url']
                    })
                    return {
                        "success": True,
                        "checkout_url": data['data'][0]['checkout_url'],
                        "order_id": ref_kode
                    }
                else:
                    logger.error(f"Transaksi gagal: {data['data']}")
                    return {"success": False, "error": data['data'][0]['status']}
            else:
                logger.error(f"Error saat membuat transaksi: {response.text}")
                return {"success": False, "error": "Gagal membuat transaksi"}

        except Exception as e:
            logger.error(f"Error saat membuat transaksi: {str(e)}")
            return {"success": False, "error": str(e)}

    def verify_transaction(self, ref_kode: str) -> dict:
        """Memverifikasi status transaksi"""
        try:
            response = requests.get(f"{self.base_url}/transactions")

            if response.status_code == 200:
                data = response.json()
                if data['status']:
                    for transaction in data['data']:
                        if transaction['ref_kode'] == ref_kode:
                            # Update status pembayaran
                            payments_col.update_one(
                                {"order_id": ref_kode},
                                {"$set": {"status": transaction['status']}}
                            )
                            return {
                                "success": True,
                                "status": transaction['status'],
                                "data": transaction
                            }
                return {"success": False, "error": "Transaksi tidak ditemukan"}
            return {"success": False, "error": "Gagal memverifikasi transaksi"}

        except Exception as e:
            logger.error(f"Error saat memverifikasi transaksi: {str(e)}")
            return {"success": False, "error": str(e)}

    def handle_callback(self, payload: dict) -> dict:
        """Menangani callback dari sistem pembayaran"""
        try:
            # Validasi signature
            callback_signature = payload.get('X-Callback-Signature')
            ref_kode = payload.get('ref_kode')
            amount = payload.get('amount')
            expected_signature = self.create_signature(ref_kode, str(amount))

            if callback_signature != expected_signature:
                logger.error("Signature tidak valid")
                return {"status": False, "message": "Signature tidak valid"}

            # Update status transaksi
            payments_col.update_one(
                {"order_id": ref_kode},
                {"$set": {"status": payload.get('status')}}
            )

            return {"status": True}

        except Exception as e:
            logger.error(f"Error saat menangani callback: {str(e)}")
            return {"status": False, "error": str(e)}

    def get_user_payments(self, user_id: int) -> list:
        """Mengambil semua riwayat pembayaran untuk pengguna"""
        return list(payments_col.find(
            {"user_id": user_id},
            sort=[("created_at", -1)]
        ))

# Instansiasi PaymentHandler
payment_gateway = PaymentHandler()

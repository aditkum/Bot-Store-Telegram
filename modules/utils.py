import os
import re
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# MongoDB Connection
client = MongoClient(os.getenv("MONGO_URI"))
db = client['vvip_bot']

class Utilities:
    """Kelas utilitas untuk fungsi-fungsi bantu"""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validasi format email"""
        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        return re.match(pattern, email) is not None

    @staticmethod
    def format_currency(amount: int) -> str:
        """Format angka ke dalam format mata uang IDR"""
        return f"Rp{amount:,.0f}".replace(",", ".")

    @staticmethod
    def log_transaction(user_id: int, action: str, details: dict):
        """Mencatat log transaksi ke database"""
        try:
            db.transaction_logs.insert_one({
                "user_id": user_id,
                "action": action,
                "details": details,
                "timestamp": datetime.now()
            })
        except Exception as e:
            logger.error(f"Gagal mencatat log transaksi: {str(e)}")

    @staticmethod
    def generate_order_id(user_id: int, product_id: str) -> str:
        """Generate ID pesanan unik"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"VVIP-{timestamp}-{user_id}-{product_id}"

    @staticmethod
    def get_product_info(product_id: str) -> dict:
        """Mengambil informasi produk dari database"""
        try:
            product = db.products.find_one({"product_id": product_id})
            if product:
                return {
                    "name": product.get("name"),
                    "price": product.get("price"),
                    "stock": product.get("stock"),
                    "description": product.get("description", "")
                }
            return None
        except Exception as e:
            logger.error(f"Error mendapatkan info produk: {str(e)}")
            return None

    @staticmethod
    def update_product_stock(product_id: str, quantity: int):
        """Update stok produk"""
        try:
            db.products.update_one(
                {"product_id": product_id},
                {"$inc": {"stock": -quantity}}
            )
        except Exception as e:
            logger.error(f"Gagal update stok produk: {str(e)}")

    @staticmethod
    def create_invoice_data(order_data: dict) -> dict:
        """Membuat data invoice untuk pembayaran"""
        return {
            "invoice_id": Utilities.generate_order_id(order_data["user_id"], order_data["product_id"]),
            "date": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "customer": {
                "user_id": order_data["user_id"],
                "username": order_data.get("username", "")
            },
            "items": [
                {
                    "product_id": order_data["product_id"],
                    "price": order_data["price"],
                    "quantity": order_data.get("quantity", 1)
                }
            ],
            "total": order_data["price"] * order_data.get("quantity", 1),
            "status": "pending"
        }

    @staticmethod
    def save_invoice(invoice_data: dict):
        """Menyimpan invoice ke database"""
        try:
            db.invoices.insert_one(invoice_data)
        except Exception as e:
            logger.error(f"Gagal menyimpan invoice: {str(e)}")

    @staticmethod
    def send_admin_notification(bot, message: str):
        """Mengirim notifikasi ke admin"""
        admin_id = os.getenv("ADMIN_ID")
        if admin_id:
            try:
                bot.send_message(chat_id=int(admin_id), text=message)
            except Exception as e:
                logger.error(f"Gagal mengirim notifikasi admin: {str(e)}")

    @staticmethod
    def validate_phone_number(phone: str) -> bool:
        """Validasi nomor telepon Indonesia"""
        pattern = r"^(\+62|62|0)8[1-9][0-9]{6,9}$"
        return re.match(pattern, phone) is not None

# Inisialisasi utilitas
utils = Utilities()

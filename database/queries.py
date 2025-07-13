from pymongo import ASCENDING, DESCENDING
from datetime import datetime, timedelta
from .models import Database
import logging

db = Database()
logger = logging.getLogger(__name__)

# ========== PRODUCT OPERATIONS ==========
def get_product(product_id: str) -> dict:
    """Ambil detail produk dari database"""
    try:
        return db.products.find_one({"product_id": product_id})
    except Exception as e:
        logger.error(f"Error getting product: {str(e)}")
        return None

def update_product_stock(product_id: str, quantity: int):
    """Update stok produk"""
    try:
        db.products.update_one(
            {"product_id": product_id},
            {"$inc": {"stock": quantity}}
        )
    except Exception as e:
        logger.error(f"Error updating stock: {str(e)}")

# ========== PAYMENT OPERATIONS ==========
def create_payment_record(user_id: int, product_id: str, amount: int, payment_url: str) -> str:
    """Buat record pembayaran baru"""
    payment_data = {
        "user_id": user_id,
        "product_id": product_id,
        "amount": amount,
        "status": "pending",
        "payment_url": payment_url,
        "created_at": datetime.now(),
        "expired_at": datetime.now() + timedelta(hours=24)
    }
    
    try:
        result = db.payments.insert_one(payment_data)
        return str(result.inserted_id)
    except Exception as e:
        logger.error(f"Error creating payment: {str(e)}")
        return None

def update_payment_status(payment_id: str, status: str):
    """Update status pembayaran"""
    valid_statuses = ["pending", "completed", "expired", "failed"]
    
    if status not in valid_statuses:
        raise ValueError(f"Invalid status. Must be one of {valid_statuses}")
    
    try:
        db.payments.update_one(
            {"_id": payment_id},
            {"$set": {"status": status, "updated_at": datetime.now()}}
        )
    except Exception as e:
        logger.error(f"Error updating payment status: {str(e)}")

def get_user_payments(user_id: int, limit: int = 5) -> list:
    """Dapatkan riwayat pembayaran user"""
    try:
        return list(db.payments.find({"user_id": user_id})
                    .sort("created_at", DESCENDING)
                    .limit(limit))
    except Exception as e:
        logger.error(f"Error fetching user payments: {str(e)}")
        return []

# ========== ADMIN QUERIES ==========
def get_daily_sales_report() -> dict:
    """Generate laporan penjualan harian"""
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    pipeline = [
        {"$match": {
            "status": "completed",
            "created_at": {"$gte": today}
        }},
        {"$group": {
            "_id": "$product_id",
            "total_sales": {"$sum": "$amount"},
            "count": {"$sum": 1}
        }}
    ]
    
    try:
        return list(db.payments.aggregate(pipeline))
    except Exception as e:
        logger.error(f"Error generating sales report: {str(e)}")
        return []

def get_recent_transactions(limit: int = 10) -> list:
    """Ambil transaksi terbaru"""
    try:
        return list(db.payments.find()
                    .sort("created_at", DESCENDING)
                    .limit(limit))
    except Exception as e:
        logger.error(f"Error fetching transactions: {str(e)}")
        return []

# ========== USER MANAGEMENT ==========
def upsert_user(user_data: dict):
    """Insert/update data user"""
    try:
        db.users.update_one(
            {"user_id": user_data["user_id"]},
            {"$set": user_data},
            upsert=True
        )
    except Exception as e:
        logger.error(f"Error upserting user: {str(e)}")

def get_active_users(days: int = 30) -> list:
    """User aktif dalam periode tertentu"""
    cutoff_date = datetime.now() - timedelta(days=days)
    
    pipeline = [
        {"$match": {
            "last_active": {"$gte": cutoff_date}
        }},
        {"$sort": {"last_active": -1}},
        {"$project": {
            "user_id": 1,
            "username": 1,
            "last_active": 1
        }}
    ]
    
    try:
        return list(db.users.aggregate(pipeline))
    except Exception as e:
        logger.error(f"Error fetching active users: {str(e)}")
        return []


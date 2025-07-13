from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

class Database:
    def __init__(self):
        self.client = MongoClient(os.getenv("MONGO_URI"))
        self.db = self.client.vvip_bot

    @property
    def products(self):
        return self.db.products
    
    @property
    def payments(self):
        return self.db.payments

def init_db():
    """Initialize sample VIP products"""
    sample_products = [
        {
            "product_id": "VVIP_1MONTH",
            "name": "VIP 1 Month Access",
            "price": 100000,
            "stock": 100
        }
    ]
    
    db = Database()
    if db.products.count_documents({}) == 0:
        db.products.insert_many(sample_products)


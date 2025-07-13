from dotenv import load_dotenv
from typing import Dict, Any
import os

load_dotenv()

class BotConfig:
    """Shared configuration across modules"""
    
    def __init__(self):
        self.TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
        self.ADMIN_ID = int(os.getenv("ADMIN_ID"))
        self.PAYMENT_CONFIG = {
            'api_key': os.getenv("PAYMENT_API_KEY"),
            'secret_key': os.getenv("PAYMENT_SECRET_KEY")
        }

def get_config() -> Dict[str, Any]:
    """Export config for dependency injection"""
    return {
        'config': BotConfig(),
        'version': '1.0.0'
    }

__all__ = ['get_config']


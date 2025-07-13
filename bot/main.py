import os
import sys
import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from bot.handlers import (
    user,  # Mengimport modul user handlers
    admin  # Mengimport modul admin handlers
)
from modules.payment_handler import payment_gateway
from database.models import init_db

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def post_init(application: Application) -> None:
    """Inisialisasi setelah bot start"""
    await application.bot.set_my_commands([
        ("start", "Mulai bot"),
        ("vip", "Beli akses VIP"),
        ("admin", "Menu admin (khusus admin)")
    ])

def main():
    # 1. Inisialisasi komponen kritis
    init_db()  # Setup database
    payment_gateway = PaymentHandler()  # Payment processor

    # 2. Buat aplikasi bot
    app = Application.builder() \
        .token(os.getenv("TELEGRAM_TOKEN")) \
        .post_init(post_init) \
        .build()

    # 3. Registrasi handlers
    # User commands
    app.add_handler(CommandHandler("start", user.start))
    app.add_handler(CommandHandler("vip", user.handle_vip))
    
    # Admin commands
    app.add_handler(CommandHandler("admin", admin.menu))
    app.add_handler(CallbackQueryHandler(admin.handle_admin_callback, pattern="^admin_"))

    # 4. Jalankan bot
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    # Memastikan environment variables terload
    from dotenv import load_dotenv
    load_dotenv()
    
    # Validasi config penting
    if not os.getenv("TELEGRAM_TOKEN"):
        logger.error("TELEGRAM_TOKEN tidak ditemukan di .env!")
        exit(1)
        
    if not os.getenv("MONGO_URI"):
        logger.warning("MONGO_URI tidak diset, menggunakan database lokal")
    
    main()

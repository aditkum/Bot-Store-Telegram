import os
import logging
from telegram.ext import Application
from bot.handlers import user, admin
from database.models import init_db

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    # Initialize
    init_db()
    
    # Create bot
    app = Application.builder().token(os.getenv("TELEGRAM_TOKEN")).build()
    
    # Register handlers
    app.add_handler(CommandHandler("start", user.start))
    app.add_handler(CommandHandler("vip", user.handle_vip))
    app.add_handler(CommandHandler("admin", admin.menu))
    
    # Run bot
    app.run_polling()

if __name__ == "__main__":
    main()

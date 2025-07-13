# /root/Bot-Store-Telegram/bot/handlers/user.py
from telegram import Update
from telegram.ext import CallbackContext
from bot.modules.payment_handler import PaymentHandler  # Perhatikan penyesuaian nama file
from bot.modules.utils import format_currency

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("👋 Welcome to VIP Bot! Use /vip to purchase")

async def handle_vip(update: Update, context: CallbackContext):
    try:
        payment = PaymentHandler()
        result = payment.create_payment(
            user_id=update.effective_user.id,
            product_id="VVIP_1MONTH",
            amount=100000
        )
        
        if 'error' not in result:
            await update.message.reply_text(
                f"💳 Payment Link: {result['payment_url']}\n"
                f"💰 Amount: {format_currency(result['amount'])}"
            )
        else:
            await update.message.reply_text("❌ Payment failed")
    
    except Exception as e:
        await update.message.reply_text(f"🚨 Error: {str(e)}")

# Ekspor handler
user = {
    'start': start,
    'handle_vip': handle_vip
}

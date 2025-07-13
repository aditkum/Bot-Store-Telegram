from telegram import Update
from telegram.ext import CallbackContext
from bot.modules.payment import PaymentHandler
from bot.modules.utils import format_currency

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "👋 Welcome to VVIP Bot!\n"
        "Use /vip to purchase VIP access"
    )

async def handle_vip(update: Update, context: CallbackContext):
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
        await update.message.reply_text("❌ Payment creation failed")


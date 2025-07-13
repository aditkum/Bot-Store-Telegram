from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from database.models import Database
from bot.modules.utils import format_currency
import os

class Admin:
   def __init__(self):
           pass

   def perform_admin_task(self):
           # Logika tugas admin
           print("Admin task performed")
   
db = Database()

async def menu(update: Update, context: CallbackContext):
    """Menu utama admin"""
    if str(update.effective_user.id) != os.getenv("ADMIN_ID"):
        await update.message.reply_text("❌ Anda bukan admin!")
        return

    keyboard = [
        [InlineKeyboardButton("📊 Statistik", callback_data="admin_stats")],
        [InlineKeyboardButton("💳 Transaksi Terbaru", callback_data="admin_transactions")],
        [InlineKeyboardButton("🔧 Maintenance", callback_data="admin_maintenance")]
    ]
    
    await update.message.reply_text(
        "🛠 *Admin Panel*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_stats(update: Update, context: CallbackContext):
    """Menampilkan statistik bot"""
    query = update.callback_query
    await query.answer()
    
    stats = {
        "total_users": db.users.count_documents({}),
        "total_transactions": db.payments.count_documents({}),
        "revenue": sum(t['amount'] for t in db.payments.find({"status": "completed"}))
    }
    
    text = (
        "📊 *Statistik Bot*\n"
        f"👥 Total User: {stats['total_users']}\n"
        f"💸 Total Transaksi: {stats['total_transactions']}\n"
        f"💰 Pendapatan: {format_currency(stats['revenue'])}"
    )
    
    await query.edit_message_text(text, parse_mode="Markdown")

async def show_recent_transactions(update: Update, context: CallbackContext):
    """Menampilkan 5 transaksi terakhir"""
    query = update.callback_query
    await query.answer()
    
    transactions = list(db.payments.find().sort("_id", -1).limit(5))
    text = "🔄 *Transaksi Terakhir*\n"
    
    for tx in transactions:
        text += (
            f"\n🆔 {tx['_id']}\n"
            f"💳 {tx.get('product_id', 'N/A')}\n"
            f"💵 {format_currency(tx.get('amount', 0))}\n"
            f"📅 {tx.get('date', 'N/A')}\n"
            f"━━━━━━━━━━━━━━━━━━━"
        )
    
    await query.edit_message_text(text, parse_mode="Markdown")

async def maintenance_menu(update: Update, context: CallbackContext):
    """Menu maintenance"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🔄 Update Produk", callback_data="update_products")],
        [InlineKeyboardButton("📝 Broadcast", callback_data="admin_broadcast")],
        [InlineKeyboardButton("🔙 Kembali", callback_data="admin_back")]
    ]
    
    await query.edit_message_text(
        "⚙️ *Maintenance Menu*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def handle_broadcast(update: Update, context: CallbackContext):
    """Handler untuk broadcast message"""
    # Implementasi broadcast ke semua user
    pass

async def back_to_admin_menu(update: Update, context: CallbackContext):
    """Kembali ke menu admin"""
    await menu(update, context)

# Callback query handler
async def handle_admin_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    
    handlers = {
        "admin_stats": show_stats,
        "admin_transactions": show_recent_transactions,
        "admin_maintenance": maintenance_menu,
        "admin_back": back_to_admin_menu
    }
    
    if data in handlers:
        await handlers[data](update, context)

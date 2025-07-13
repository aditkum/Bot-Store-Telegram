import os
import logging
from datetime import datetime
from bot.modules.payment_handler import payment_gateway
from bot.modules.utils import utils
from pymongo import MongoClient, ASCENDING
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputTextMessageContent
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    InlineQueryHandler,
    MessageHandler,
    filters,
    CallbackContext
)
from dotenv import load_dotenv

# Memuat variabel lingkungan dari file .env
load_dotenv()

# Mengakses variabel lingkungan
api_key = os.getenv("VIOLET_API_KEY")
secret_key = os.getenv("VIOLET_SECRET_KEY")

# --- Configuration ---
OWNER_ID = 1749723307
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")

# Initialize MongoDB
client = MongoClient(MONGO_URI)
db = client['telegram_vvip_store']
produk_col = db['produk']
riwayat_col = db['riwayat']
statistik_col = db['statistik']
inline_messages_col = db['inline_messages']

# Pastikan index sudah dibuat
db.payments.create_index([("user_id", ASCENDING)])
db.payments.create_index([("status", ASCENDING)])
db.users.create_index([("user_id", ASCENDING)], unique=True)

# --- Logging ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Utility Functions ---
def get_produk():
    return {str(item['_id']): item for item in produk_col.find()}

def update_produk(produk_id, update_data):
    produk_col.update_one({'_id': produk_id}, {'$set': update_data})

def add_riwayat(uid, tipe, keterangan, jumlah):
    riwayat_col.insert_one({
        "user_id": uid,
        "tipe": tipe,
        "keterangan": keterangan,
        "jumlah": jumlah,
        "waktu": datetime.now()
    })

def update_statistik(uid, nominal):
    statistik_col.update_one(
        {"user_id": uid},
        {"$inc": {"jumlah": 1, "nominal": nominal}},
        upsert=True
    )

def add_inline_message(title, content, url):
    return inline_messages_col.insert_one({
        "title": title,
        "content": content,
        "url": url,
        "created_at": datetime.now()
    }).inserted_id

# --- Inline Query Handler ---
async def handle_inline_query(update: Update, context: CallbackContext):
    query = update.inline_query.query.lower()
    results = []
    
    # Get products from database
    products = list(produk_col.find({
        "$or": [
            {"nama": {"$regex": query, "$options": "i"}},
            {"deskripsi": {"$regex": query, "$options": "i"}}
        ]
    }).limit(50))

    for product in products:
        results.append(
            InlineQueryResultArticle(
                id=str(product['_id']),
                title=product['nama'],
                description=f"Rp{product['harga']:,} | Stok: {product['stok']}",
                input_message_content=InputTextMessageContent(
                    message_text=f"🛒 *{product['nama']}*\n"
                                 f"💰 Harga: Rp{product['harga']:,}\n"
                                 f"📦 Stok: {product['stok']}\n\n"
                                 f"{product.get('deskripsi', '')}",
                    parse_mode="Markdown"
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        "💳 Beli Sekarang",
                        callback_data=f"buy_{product['_id']}"
                    )]
                ]),
                thumb_url="https://placehold.co/100?text=VIP"
            )
        )
    
    await update.inline_query.answer(results, cache_time=0)

# --- Admin Commands ---
async def handle_add_inline(update: Update, context: CallbackContext):
    if update.effective_user.id != OWNER_ID:
        return
    
    args = context.args
    if len(args) < 3:
        await update.message.reply_text("Format: /addinline <judul> <url> <konten>")
        return
    
    title = args[0]
    url = args[1]
    content = " ".join(args[2:])
    
    add_inline_message(title, content, url)
    await update.message.reply_text("✅ Pesan inline berhasil ditambahkan!")

# --- Main Bot Handlers ---
async def send_main_menu(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "🏆 VIP GROUP ACCESS BOT\n\n"
        "Pilih menu dibawah:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📦 List Produk", callback_data="list_produk")],
            [InlineKeyboardButton("ℹ Info Bot", callback_data="info_bot")],
            [InlineKeyboardButton("🔍 Cari Produk", switch_inline_query_current_chat="")]
        ])
    )

async def handle_list_produk(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    products = list(produk_col.find({}).sort("nama", 1))
    
    keyboard = []
    for product in products:
        status = "✅" if product['stok'] > 0 else "❌"
        keyboard.append([
            InlineKeyboardButton(
                f"{status} {product['nama']} - Rp{product['harga']:,}",
                callback_data=f"detail_{product['_id']}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Kembali", callback_data="back_to_menu")])
    
    await query.edit_message_text(
        "📋 DAFTAR PRODUK VVIP",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_detail_produk(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    product_id = query.data.split("_")[1]
    product = produk_col.find_one({"_id": product_id})
    
    text = f"""
🛒 *{product['nama']}*
💰 Harga: Rp{product['harga']:,}
📦 Stok: {product['stok']}

{product.get('deskripsi', '')}
"""
    keyboard = [
        [InlineKeyboardButton("➕ Tambah ke Keranjang", callback_data=f"add_{product_id}")],
        [InlineKeyboardButton("🔙 Kembali", callback_data="list_produk")]
    ]
    
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# --- Payment Integration ---
async def handle_payment(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    # This would integrate with your payment gateway
    payment_url = "https://payment-gateway.example.com/pay"
    
    await query.edit_message_text(
        f"✅ Silakan lanjutkan pembayaran di:\n{payment_url}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Kembali", callback_data="list_produk")]
        ])
    )

# --- Main Application ---
def main():
    application = Application.builder().token(os.getenv("TELEGRAM_TOKEN")).build()
    
    # Command Handlers
    application.add_handler(CommandHandler("start", send_main_menu))
    application.add_handler(CommandHandler("addinline", handle_add_inline))
    
    # Callback Handlers
    application.add_handler(CallbackQueryHandler(handle_list_produk, pattern="^list_produk$"))
    application.add_handler(CallbackQueryHandler(handle_detail_produk, pattern="^detail_"))
    application.add_handler(CallbackQueryHandler(handle_payment, pattern="^buy_"))
    
    # Inline Handler
    application.add_handler(InlineQueryHandler(handle_inline_query))
    
    # Message Handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, send_main_menu))
    
    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()

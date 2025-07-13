from telegram import Bot
from static.templates.admin_alert import admin_alert_template

def send_admin_alert(transaction):
    bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
    message = admin_alert_template.format(
        transaction_id=transaction['_id'],
        user_id=transaction['user_id'],
        username=transaction.get('username', 'N/A'),
        product_name=transaction['product_id'],
        amount=format_currency(transaction['amount']),
        status=transaction['status'],
        timestamp=transaction['created_at'].strftime("%Y-%m-%d %H:%M:%S"),
        payment_method=transaction.get('payment_method', 'N/A'),
        payment_url=transaction.get('payment_url', '#')
    )
    
    bot.send_message(chat_id=os.getenv("ADMIN_ID"), text=message, parse_mode='Markdown')


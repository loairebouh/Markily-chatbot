import logging
import sqlite3
from datetime import datetime
from typing import Optional, List, Tuple
import re
import os
from difflib import get_close_matches

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler,
    ContextTypes,
    filters
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class MarkilyBot:
    def __init__(self, bot_token: str, db_path: str = "/app/data/markily.db"):
        self.bot_token = bot_token
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_database()
    
    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT NOT NULL,
                phone TEXT,
                telegram_username TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (telegram_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                contact_id INTEGER,
                amount REAL NOT NULL,
                currency TEXT DEFAULT 'DZD',
                transaction_type TEXT NOT NULL,
                note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (telegram_id),
                FOREIGN KEY (contact_id) REFERENCES contacts (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_user_contacts(self, user_id: int) -> List[Tuple]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, name, phone, telegram_username 
            FROM contacts 
            WHERE user_id = ?
            ORDER BY name
        ''', (user_id,))
        contacts = cursor.fetchall()
        conn.close()
        return contacts
    
    def search_contact(self, user_id: int, search_term: str) -> Optional[Tuple]:
        contacts = self.get_user_contacts(user_id)
        contact_names = [contact[1].lower() for contact in contacts]
        
        for i, contact in enumerate(contacts):
            if contact[1].lower() == search_term.lower():
                return contact
        
        matches = get_close_matches(search_term.lower(), contact_names, n=1, cutoff=0.6)
        if matches:
            for contact in contacts:
                if contact[1].lower() == matches[0]:
                    return contact
        
        return None
    
    def add_contact(self, user_id: int, name: str, phone: str = None, telegram_username: str = None) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO contacts (user_id, name, phone, telegram_username)
            VALUES (?, ?, ?, ?)
        ''', (user_id, name, phone, telegram_username))
        contact_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return contact_id
    
    def add_transaction(self, user_id: int, contact_id: int, amount: float, 
                       currency: str, transaction_type: str, note: str = None) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO transactions (user_id, contact_id, amount, currency, transaction_type, note)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, contact_id, amount, currency, transaction_type, note))
        transaction_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return transaction_id
    
    def get_balance(self, user_id: int, contact_id: int) -> Tuple[float, str]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT amount, transaction_type, currency FROM transactions
            WHERE user_id = ? AND contact_id = ?
            ORDER BY created_at
        ''', (user_id, contact_id))
        
        transactions = cursor.fetchall()
        conn.close()
        
        if not transactions:
            return 0.0, 'DZD'
        
        balance = 0.0
        currency = transactions[0][2]
        
        for amount, transaction_type, _ in transactions:
            if transaction_type == 'lend':
                balance += amount
            else:
                balance -= amount
        
        return balance, currency
    
    def get_transaction_history(self, user_id: int, contact_id: int) -> List[Tuple]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT amount, currency, transaction_type, note, created_at
            FROM transactions
            WHERE user_id = ? AND contact_id = ?
            ORDER BY created_at DESC
        ''', (user_id, contact_id))
        history = cursor.fetchall()
        conn.close()
        return history
    
    def register_user(self, user_id: int, username: str = None, 
                     first_name: str = None, last_name: str = None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO users (telegram_id, username, first_name, last_name)
            VALUES (?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name))
        conn.commit()
        conn.close()

bot = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    bot.register_user(user.id, user.username, user.first_name, user.last_name)
    
    welcome_message = f"""
🏦 **Welcome to Markily Debt Manager!**

Hi {user.first_name}! I'll help you track money you lend and borrow with your contacts.

**Available Commands:**
/addcontact - Add a new contact
/contacts - View all contacts
/lend - Record money you lent
/borrow - Record money you borrowed
/balance - Check balance with someone
/history - View transaction history
/clear - Clear balance with someone
/help - Show this help message

**Example Usage:**
`/lend amine 1000 DZD lunch money`
`/balance amine`
`/history amine`
    """
    
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
🔹 **Commands Guide:**

**Managing Contacts:**
• `/addcontact Name Phone` - Add contact
• `/contacts` - List all contacts

**Recording Transactions:**
• `/lend contact amount currency note` - Record money lent
• `/borrow contact amount currency note` - Record money borrowed

**Checking Status:**
• `/balance contact` - Check net balance
• `/history contact` - View all transactions
• `/clear contact amount currency note` - Clear balance

**Examples:**
• `/lend amine 1000 DZD lunch money`
• `/borrow sara 500 DZD taxi fare`
• `/balance amine`
• `/clear amine 6000 DZD final payment`

💡 **Tips:**
- You can use partial names (e.g., "ami" for "Amine")
- Currency defaults to DZD if not specified
- Notes are optional but recommended
    """
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def add_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Usage: `/addcontact Name [Phone]`\nExample: `/addcontact Amine Khoudor +213123456789`",
            parse_mode='Markdown'
        )
        return
    
    name = " ".join(context.args[:-1]) if len(context.args) > 1 else context.args[0]
    phone = context.args[-1] if len(context.args) > 1 and context.args[-1].startswith('+') else None
    
    if phone and not name:
        name = context.args[0]
        phone = None
    
    contact_id = bot.add_contact(update.effective_user.id, name, phone)
    
    await update.message.reply_text(
        f"✅ Contact **{name}** added successfully!",
        parse_mode='Markdown'
    )

async def list_contacts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contacts = bot.get_user_contacts(update.effective_user.id)
    
    if not contacts:
        await update.message.reply_text("📭 You don't have any contacts yet. Use `/addcontact` to add one!", parse_mode='Markdown')
        return
    
    message = "👥 **Your Contacts:**\n\n"
    for contact in contacts:
        contact_id, name, phone, telegram_username = contact
        balance, currency = bot.get_balance(update.effective_user.id, contact_id)
        
        status = ""
        if balance > 0:
            status = f" (owes you {balance:,.0f} {currency})"
        elif balance < 0:
            status = f" (you owe {abs(balance):,.0f} {currency})"
        else:
            status = " (settled)"
        
        phone_info = f" - {phone}" if phone else ""
        message += f"• **{name}**{phone_info}{status}\n"
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def lend_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text(
            "Usage: `/lend contact amount [currency] [note]`\nExample: `/lend amine 1000 DZD lunch money`",
            parse_mode='Markdown'
        )
        return
    
    contact_search = context.args[0]
    
    try:
        amount = float(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid amount!")
        return
    
    currency = "DZD"
    note = ""
    
    if len(context.args) > 2:
        if context.args[2].upper() in ['DZD', 'USD', 'EUR', 'DA']:
            currency = context.args[2].upper()
            if currency == 'DA':
                currency = 'DZD'
            note = " ".join(context.args[3:]) if len(context.args) > 3 else ""
        else:
            note = " ".join(context.args[2:])
    
    contact = bot.search_contact(update.effective_user.id, contact_search)
    
    if not contact:
        keyboard = [
            [InlineKeyboardButton("Yes, add contact", callback_data=f"add_contact_{contact_search}_{amount}_{currency}_{note}")],
            [InlineKeyboardButton("No, cancel", callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"❓ Contact '{contact_search}' not found. Would you like to add them?",
            reply_markup=reply_markup
        )
        return
    
    contact_id, contact_name = contact[0], contact[1]
    
    bot.add_transaction(update.effective_user.id, contact_id, amount, currency, 'lend', note)
    
    balance, _ = bot.get_balance(update.effective_user.id, contact_id)
    
    note_text = f" ({note})" if note else ""
    balance_text = ""
    if balance > 0:
        balance_text = f"\n💰 **{contact_name}** now owes you **{balance:,.0f} {currency}**"
    elif balance < 0:
        balance_text = f"\n💰 You now owe **{contact_name}** **{abs(balance):,.0f} {currency}**"
    else:
        balance_text = f"\n✅ You and **{contact_name}** are now settled"
    
    await update.message.reply_text(
        f"✅ Recorded: You lent **{amount:,.0f} {currency}** to **{contact_name}**{note_text}{balance_text}",
        parse_mode='Markdown'
    )

async def borrow_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text(
            "Usage: `/borrow contact amount [currency] [note]`\nExample: `/borrow sara 2000 DZD car repair`",
            parse_mode='Markdown'
        )
        return
    
    contact_search = context.args[0]
    
    try:
        amount = float(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid amount!")
        return
    
    currency = "DZD"
    note = ""
    
    if len(context.args) > 2:
        if context.args[2].upper() in ['DZD', 'USD', 'EUR', 'DA']:
            currency = context.args[2].upper()
            if currency == 'DA':
                currency = 'DZD'
            note = " ".join(context.args[3:]) if len(context.args) > 3 else ""
        else:
            note = " ".join(context.args[2:])
    
    contact = bot.search_contact(update.effective_user.id, contact_search)
    
    if not contact:
        keyboard = [
            [InlineKeyboardButton("Yes, add contact", callback_data=f"add_contact_borrow_{contact_search}_{amount}_{currency}_{note}")],
            [InlineKeyboardButton("No, cancel", callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"❓ Contact '{contact_search}' not found. Would you like to add them?",
            reply_markup=reply_markup
        )
        return
    
    contact_id, contact_name = contact[0], contact[1]
    
    bot.add_transaction(update.effective_user.id, contact_id, amount, currency, 'borrow', note)
    
    balance, _ = bot.get_balance(update.effective_user.id, contact_id)
    
    note_text = f" ({note})" if note else ""
    balance_text = ""
    if balance > 0:
        balance_text = f"\n💰 **{contact_name}** now owes you **{balance:,.0f} {currency}**"
    elif balance < 0:
        balance_text = f"\n💰 You now owe **{contact_name}** **{abs(balance):,.0f} {currency}**"
    else:
        balance_text = f"\n✅ You and **{contact_name}** are now settled"
    
    await update.message.reply_text(
        f"✅ Recorded: You borrowed **{amount:,.0f} {currency}** from **{contact_name}**{note_text}{balance_text}",
        parse_mode='Markdown'
    )

async def check_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Usage: `/balance contact`\nExample: `/balance amine`",
            parse_mode='Markdown'
        )
        return
    
    contact_search = context.args[0]
    contact = bot.search_contact(update.effective_user.id, contact_search)
    
    if not contact:
        await update.message.reply_text(f"❌ Contact '{contact_search}' not found!")
        return
    
    contact_id, contact_name = contact[0], contact[1]
    balance, currency = bot.get_balance(update.effective_user.id, contact_id)
    
    if balance > 0:
        message = f"💰 **{contact_name}** owes you **{balance:,.0f} {currency}**"
    elif balance < 0:
        message = f"💰 You owe **{contact_name}** **{abs(balance):,.0f} {currency}**"
    else:
        message = f"✅ You and **{contact_name}** are settled (no outstanding balance)"
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def transaction_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Usage: `/history contact`\nExample: `/history amine`",
            parse_mode='Markdown'
        )
        return
    
    contact_search = context.args[0]
    contact = bot.search_contact(update.effective_user.id, contact_search)
    
    if not contact:
        await update.message.reply_text(f"❌ Contact '{contact_search}' not found!")
        return
    
    contact_id, contact_name = contact[0], contact[1]
    history = bot.get_transaction_history(update.effective_user.id, contact_id)
    
    if not history:
        await update.message.reply_text(f"📭 No transactions found with **{contact_name}**", parse_mode='Markdown')
        return
    
    message = f"📊 **Transaction History with {contact_name}:**\n\n"
    
    for amount, currency, transaction_type, note, created_at in history:
        date = datetime.fromisoformat(created_at).strftime("%Y-%m-%d %H:%M")
        
        if transaction_type == 'lend':
            emoji = "🔴"
            action = "You lent"
        else:
            emoji = "🔵" 
            action = "You borrowed"
        
        note_text = f" - {note}" if note else ""
        message += f"{emoji} {action} **{amount:,.0f} {currency}**{note_text}\n   _{date}_\n\n"
    
    balance, currency = bot.get_balance(update.effective_user.id, contact_id)
    if balance > 0:
        message += f"💰 **Current Balance:** {contact_name} owes you **{balance:,.0f} {currency}**"
    elif balance < 0:
        message += f"💰 **Current Balance:** You owe {contact_name} **{abs(balance):,.0f} {currency}**"
    else:
        message += f"✅ **Current Balance:** Settled"
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def clear_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text(
            "Usage: `/clear contact amount [currency] [note]`\nExample: `/clear amine 6000 DZD final payment`",
            parse_mode='Markdown'
        )
        return
    
    contact_search = context.args[0]
    
    try:
        amount = float(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid amount!")
        return
    
    currency = "DZD"
    note = "Balance cleared"
    
    if len(context.args) > 2:
        if context.args[2].upper() in ['DZD', 'USD', 'EUR', 'DA']:
            currency = context.args[2].upper()
            if currency == 'DA':
                currency = 'DZD'
            note = " ".join(context.args[3:]) if len(context.args) > 3 else "Balance cleared"
        else:
            note = " ".join(context.args[2:])
    
    contact = bot.search_contact(update.effective_user.id, contact_search)
    
    if not contact:
        await update.message.reply_text(f"❌ Contact '{contact_search}' not found!")
        return
    
    contact_id, contact_name = contact[0], contact[1]
    
    current_balance, _ = bot.get_balance(update.effective_user.id, contact_id)
    
    if current_balance > 0:
        transaction_type = 'borrow'
    else:
        transaction_type = 'lend'
    
    bot.add_transaction(update.effective_user.id, contact_id, amount, currency, transaction_type, note)
    
    new_balance, _ = bot.get_balance(update.effective_user.id, contact_id)
    
    message = f"✅ Recorded payment of **{amount:,.0f} {currency}** with **{contact_name}**"
    if note != "Balance cleared":
        message += f" ({note})"
    
    if abs(new_balance) < 0.01:
        message += f"\n🎉 You and **{contact_name}** are now settled!"
    else:
        if new_balance > 0:
            message += f"\n💰 **{contact_name}** still owes you **{new_balance:,.0f} {currency}**"
        else:
            message += f"\n💰 You still owe **{contact_name}** **{abs(new_balance):,.0f} {currency}**"
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "cancel":
        await query.edit_message_text("❌ Operation cancelled.")
        return
    
    if data.startswith("add_contact_"):
        parts = data.split("_", 3)
        if len(parts) >= 4:
            contact_name = parts[2]
            
            contact_id = bot.add_contact(query.from_user.id, contact_name)
            
            await query.edit_message_text(f"✅ Contact **{contact_name}** added! Please run your command again.", parse_mode='Markdown')

async def main():
    global bot
    
    BOT_TOKEN = os.getenv('BOT_TOKEN', '8315987255:AAHsBw4_8UtkfF79nRZKnT5lNMzNxOWvk9s')
    
    if BOT_TOKEN == "8315987255:AAHsBw4_8UtkfF79nRZKnT5lNMzNxOWvk9s" or not BOT_TOKEN:
        print("❌ Please set BOT_TOKEN environment variable with your actual token from @BotFather")
        print("💡 Get your token by messaging @BotFather on Telegram")
        return
    
    bot = MarkilyBot(BOT_TOKEN)
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    await application.initialize()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("addcontact", add_contact))
    application.add_handler(CommandHandler("contacts", list_contacts))
    application.add_handler(CommandHandler("lend", lend_money))
    application.add_handler(CommandHandler("borrow", borrow_money))
    application.add_handler(CommandHandler("balance", check_balance))
    application.add_handler(CommandHandler("history", transaction_history))
    application.add_handler(CommandHandler("clear", clear_balance))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    print("🚀 Markily Bot is starting...")
    await application.start()
    await application.updater.start_polling()
    
    try:
        import asyncio
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        print("\n👋 Shutting down Markily Bot...")
    finally:
        await application.updater.stop()
        await application.stop()
        await application.shutdown()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
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
    ConversationHandler,
    filters
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

WAITING_FOR_CONTACT_NAME, WAITING_FOR_AMOUNT, WAITING_FOR_NOTE = range(3)

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
    
    keyboard = [
        [
            InlineKeyboardButton("💸 I Lent Money", callback_data="action_lend"),
            InlineKeyboardButton("💰 I Borrowed Money", callback_data="action_borrow")
        ],
        [
            InlineKeyboardButton("👤 Add Contact", callback_data="action_add_contact"),
            InlineKeyboardButton("📊 View Balances", callback_data="action_balances")
        ],
        [
            InlineKeyboardButton("📜 Transaction History", callback_data="action_history"),
            InlineKeyboardButton("✅ Clear Balance", callback_data="action_clear")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = f"🏦 **Welcome {user.first_name}!**\n\nChoose what you want to do:"
    
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.callback_query.edit_message_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_contacts_for_action(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str):
    query = update.callback_query
    await query.answer()
    
    contacts = bot.get_user_contacts(query.from_user.id)
    
    if not contacts:
        keyboard = [
            [InlineKeyboardButton("👤 Add Contact First", callback_data="action_add_contact")],
            [InlineKeyboardButton("� Back to Menu", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📭 You don't have any contacts yet!\nAdd a contact first to continue.",
            reply_markup=reply_markup
        )
        return
    
    keyboard = []
    for contact in contacts:
        contact_id, name, phone, telegram_username = contact
        balance, currency = bot.get_balance(query.from_user.id, contact_id)
        
        status = ""
        if balance > 0:
            status = f" (owes {balance:,.0f})"
        elif balance < 0:
            status = f" (you owe {abs(balance):,.0f})"
        
        button_text = f"{name}{status}"
        callback_data = f"{action}_{contact_id}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
    
    keyboard.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    action_text = {
        "lend": "💸 Who did you lend money to?",
        "borrow": "💰 Who did you borrow money from?",
        "clear": "✅ Clear balance with whom?",
        "history": "📜 View history with whom?"
    }
    
    await query.edit_message_text(
        action_text.get(action, "👥 Choose a contact:"),
        reply_markup=reply_markup
    )

async def handle_contact_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    action, contact_id = data.split('_', 1)
    
    context.user_data['action'] = action
    context.user_data['contact_id'] = int(contact_id)
    
    contact = next((c for c in bot.get_user_contacts(query.from_user.id) if c[0] == int(contact_id)), None)
    if not contact:
        await query.edit_message_text("❌ Contact not found!")
        return ConversationHandler.END
    
    context.user_data['contact_name'] = contact[1]
    
    if action == "history":
        await show_transaction_history(update, context)
        return ConversationHandler.END
    
    action_text = {
        "lend": f"💸 How much did you lend to **{contact[1]}**?",
        "borrow": f"💰 How much did you borrow from **{contact[1]}**?",
        "clear": f"✅ How much did you pay to **{contact[1]}**?"
    }
    
    keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"{action_text.get(action, 'Enter amount:')}\n\n💡 Send just the number (e.g., 1000)",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return WAITING_FOR_AMOUNT

async def handle_amount_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text.strip())
        if amount <= 0:
            raise ValueError("Amount must be positive")
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid positive number (e.g., 1000)")
        return WAITING_FOR_AMOUNT
    
    context.user_data['amount'] = amount
    action = context.user_data['action']
    contact_name = context.user_data['contact_name']
    
    action_text = {
        "lend": f"💸 You lent **{amount:,.0f} DZD** to **{contact_name}**",
        "borrow": f"💰 You borrowed **{amount:,.0f} DZD** from **{contact_name}**",
        "clear": f"✅ You paid **{amount:,.0f} DZD** to **{contact_name}**"
    }
    
    keyboard = [
        [
            InlineKeyboardButton("💾 Save (No Note)", callback_data="save_transaction_no_note"),
            InlineKeyboardButton("📝 Add Note", callback_data="add_note")
        ],
        [InlineKeyboardButton("❌ Cancel", callback_data="back_to_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"{action_text.get(action, '')}\n\nDo you want to add a note?",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return WAITING_FOR_NOTE

async def handle_note_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    note = update.message.text.strip()
    context.user_data['note'] = note
    
    await save_transaction_and_finish(update, context)
    return ConversationHandler.END

async def save_transaction_and_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    action = context.user_data['action']
    contact_id = context.user_data['contact_id']
    contact_name = context.user_data['contact_name']
    amount = context.user_data['amount']
    note = context.user_data.get('note', '')
    
    user_id = update.effective_user.id
    
    if action == "clear":
        current_balance, _ = bot.get_balance(user_id, contact_id)
        transaction_type = 'borrow' if current_balance > 0 else 'lend'
    else:
        transaction_type = action
    
    bot.add_transaction(user_id, contact_id, amount, 'DZD', transaction_type, note)
    
    balance, currency = bot.get_balance(user_id, contact_id)
    
    note_text = f" ({note})" if note else ""
    
    action_emoji = {"lend": "💸", "borrow": "💰", "clear": "✅"}
    action_verb = {"lend": "lent to", "borrow": "borrowed from", "clear": "paid to"}
    
    message = f"{action_emoji.get(action, '')} **Transaction recorded!**\n\n"
    message += f"You {action_verb.get(action, '')} **{contact_name}**: {amount:,.0f} DZD{note_text}\n\n"
    
    if abs(balance) < 0.01:
        message += f"🎉 You and **{contact_name}** are now settled!"
    elif balance > 0:
        message += f"💰 **{contact_name}** owes you **{balance:,.0f} {currency}**"
    else:
        message += f"💰 You owe **{contact_name}** **{abs(balance):,.0f} {currency}**"
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def show_transaction_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    contact_id = context.user_data['contact_id']
    contact_name = context.user_data['contact_name']
    
    history = bot.get_transaction_history(update.effective_user.id, contact_id)
    
    if not history:
        message = f"📭 No transactions found with **{contact_name}**"
    else:
        message = f"� **History with {contact_name}:**\n\n"
        
        for amount, currency, transaction_type, note, created_at in history[:10]:
            date = datetime.fromisoformat(created_at).strftime("%m/%d")
            
            if transaction_type == 'lend':
                emoji = "💸"
                action = "You lent"
            else:
                emoji = "💰" 
                action = "You borrowed"
            
            note_text = f" - {note}" if note else ""
            message += f"{emoji} {action} {amount:,.0f} {currency}{note_text} ({date})\n"
        
        balance, currency = bot.get_balance(update.effective_user.id, contact_id)
        message += f"\n**Current Balance:**\n"
        if balance > 0:
            message += f"💰 {contact_name} owes you {balance:,.0f} {currency}"
        elif balance < 0:
            message += f"💰 You owe {contact_name} {abs(balance):,.0f} {currency}"
        else:
            message += f"✅ Settled"
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def show_all_balances(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    contacts = bot.get_user_contacts(query.from_user.id)
    
    if not contacts:
        keyboard = [
            [InlineKeyboardButton("👤 Add Contact", callback_data="action_add_contact")],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📭 You don't have any contacts yet!",
            reply_markup=reply_markup
        )
        return
    
    message = "📊 **Your Balances:**\n\n"
    
    for contact in contacts:
        contact_id, name, phone, telegram_username = contact
        balance, currency = bot.get_balance(query.from_user.id, contact_id)
        
        if balance > 0:
            message += f"💰 **{name}** owes you **{balance:,.0f} {currency}**\n"
        elif balance < 0:
            message += f"💸 You owe **{name}** **{abs(balance):,.0f} {currency}**\n"
        else:
            message += f"✅ **{name}** - settled\n"
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def start_add_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "👤 **Add New Contact**\n\nSend me the contact's name:\n\n💡 Example: Ahmed Benali",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return WAITING_FOR_CONTACT_NAME

async def handle_contact_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    
    if len(name) < 2:
        await update.message.reply_text("❌ Name must be at least 2 characters long")
        return WAITING_FOR_CONTACT_NAME
    
    contact_id = bot.add_contact(update.effective_user.id, name)
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"✅ **{name}** added to your contacts!",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return ConversationHandler.END

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "back_to_menu":
        await start(update, context)
        return ConversationHandler.END
    
    elif data == "action_add_contact":
        return await start_add_contact(update, context)
    
    elif data == "action_balances":
        await show_all_balances(update, context)
        return ConversationHandler.END
    
    elif data == "action_lend":
        await show_contacts_for_action(update, context, "lend")
        return ConversationHandler.END
    
    elif data == "action_borrow":
        await show_contacts_for_action(update, context, "borrow")
        return ConversationHandler.END
    
    elif data == "action_clear":
        await show_contacts_for_action(update, context, "clear")
        return ConversationHandler.END
    
    elif data == "action_history":
        await show_contacts_for_action(update, context, "history")
        return ConversationHandler.END
    
    elif data.startswith(("lend_", "borrow_", "clear_", "history_")):
        return await handle_contact_selection(update, context)
    
    elif data == "save_transaction_no_note":
        context.user_data['note'] = ''
        await save_transaction_and_finish(update, context)
        return ConversationHandler.END
    
    elif data == "add_note":
        keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📝 Send me a note for this transaction:\n\n💡 Example: lunch money, taxi fare, etc.",
            reply_markup=reply_markup
        )
        return WAITING_FOR_NOTE
    
    return ConversationHandler.END

async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)
    return ConversationHandler.END

async def main():
    global bot
    
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    
    if not BOT_TOKEN:
        print("❌ Please set BOT_TOKEN environment variable with your actual token from @BotFather")
        print("💡 Get your token by messaging @BotFather on Telegram")
        return
    
    bot = MarkilyBot(BOT_TOKEN)
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    await application.initialize()
    
    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(button_callback, pattern="^action_add_contact$"),
            CallbackQueryHandler(button_callback, pattern="^(lend|borrow|clear|history)_"),
        ],
        states={
            WAITING_FOR_CONTACT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_contact_name_input)],
            WAITING_FOR_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_amount_input)],
            WAITING_FOR_NOTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_note_input)],
        },
        fallbacks=[
            CallbackQueryHandler(cancel_conversation, pattern="^back_to_menu$"),
            CommandHandler("start", start),
        ],
    )
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)
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
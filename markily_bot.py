import logging
import sqlite3
from datetime import datetime
from typing import Optional, List, Tuple
import re
import os
from difflib import get_close_matches
from dotenv import load_dotenv

load_dotenv()

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

# Language translations
TRANSLATIONS = {
    'en': {
        'welcome': "🏦 **Welcome {}!**\n\nChoose what you want to do:",
        'lent_money': "↗️ + I Lent Money to",
        'borrowed_money': "↙️ -  I Borrowed Money from ",
        'add_contact': "👤 Add Contact",
        'view_balances': "📊 View Balances",
        'transaction_history': "📜 Transaction History",
        'clear_balance': "✅ Clear Balance",
        'delete_contact': "🗑️ Delete Contact",
        'language': "🌐 Language",
        'back_to_menu': "🔙 Back to Menu",
        'cancel': "❌ Cancel",
        'no_contacts': "📭 You don't have any contacts yet!\nAdd a contact first to continue.",
        'no_contacts_delete': "📭 You don't have any contacts to delete!",
        'add_contact_first': "👤 Add Contact First",
        'who_lent_to': "↗️ Who did you lend money to?",
        'who_borrowed_from': "↙️ Who did you borrow money from?",
        'clear_balance_with': "✅ Clear balance with whom?",
        'view_history_with': "📜 View history with whom?",
        'contact_not_found': "❌ Contact not found!",
        'how_much_lent': "↗️ How much did you lend to **{}**?",
        'how_much_borrowed': "↙️ How much did you borrow from **{}**?",
        'how_much_paid': "✅ How much did you pay to **{}**?",
        'enter_amount_hint': "\n\n💡 Send just the number (e.g., 1000)",
        'invalid_amount': "❌ Please enter a valid positive number (e.g., 1000)",
        'you_lent': "↗️ You lent **{:,.0f} DZD** to **{}**",
        'you_borrowed': "↙️ You borrowed **{:,.0f} DZD** from **{}**",
        'you_paid': "✅ You paid **{:,.0f} DZD** to **{}**",
        'add_note_question': "\n\nDo you want to add a note?",
        'save_no_note': "💾 Save (No Note)",
        'add_note': "📝 Add Note",
        'transaction_recorded': "**Transaction recorded!**",
        'lent_to': "lent to",
        'borrowed_from': "borrowed from",
        'paid_to': "paid to",
        'settled': "🎉 You and **{}** are now settled!",
        'owes_you': "↗️ **{}** owes you **{:,.0f} {}**",
        'you_owe': "↙️ You owe **{}** **{:,.0f} {}**",
        'no_transactions': "📭 No transactions found with **{}**",
        'history_with': "📜 **History with {}:**",
        'you_lent_history': "You lent",
        'you_borrowed_history': "You borrowed",
        'current_balance': "**Current Balance:**",
        'settled_balance': "✅ Settled",
        'your_balances': "📊 **Your Balances:**",
        'total_balance': "💯 **TOTAL BALANCE:**",
        'net_positive': "💰 **Net: +{:,.0f} DZD**\n_You are owed more than you owe_",
        'net_negative': "❌ **Net: {:,.0f} DZD**\n_You owe more than you are owed_",
        'net_zero': "✅ **Net: 0 DZD**\n_All balances are settled_",
        'delete_contact_title': "🗑️ **Delete Contact**\n\n⚠️ Choose a contact to delete.\nThis will also delete all transaction history!",
        'delete_confirmation': "🗑️ **Delete Contact**\n\nAre you sure you want to delete **{}**?{}\n\nThis action cannot be undone!",
        'warning_owes_you': "\n⚠️ **Warning:** {} owes you {:,.0f} {}!",
        'warning_you_owe': "\n⚠️ **Warning:** You owe {} {:,.0f} {}!",
        'delete_success': "✅ **{}** has been deleted!\n\nAll transaction history has been removed.",
        'delete_failed': "❌ Failed to delete **{}**.",
        'add_new_contact': "👤 **Add New Contact**\n\nSend me the contact's name:\n\n💡 Example: Ahmed Benali",
        'name_too_short': "❌ Name must be at least 2 characters long",
        'contact_added': "✅ **{}** added to your contacts!",
        'send_note': "📝 Send me a note for this transaction:\n\n💡 Example: lunch money, taxi fare, etc.",
        'choose_language': "🌐 **Choose Language / اختر اللغة**",
        'owes_short': "(owes {:,.0f})",
        'you_owe_short': "(you owe {:,.0f})",
        'analytics': "📊 Analytics",
        'total_users': "👥 Total Users: {}",
        'active_today': "🔥 Active Today: {}",
        'new_users_today': "🆕 New Users Today: {}",
        'total_transactions': "💼 Total Transactions: {}",
        'total_chats': "💬 Total Chats: {}",
        'language_stats': "🌐 Language Distribution:",
        'analytics_summary': "📊 **Bot Analytics**\n\n{}\n{}\n{}\n{}\n{}\n\n{}\n{}",
        'group_mode': "👥 Group Mode: Data is separate for each chat",
        'private_mode': "👤 Private Mode: Personal data only"
    },
    'ar': {
        'welcome': "🏦 **مرحباً {}!**\n\nاختر ما تريد فعله:",
        'lent_money': "↗️ أقرضت مالاً",
        'borrowed_money': "↙️ استدنت مالاً", 
        'add_contact': "👤 إضافة جهة اتصال",
        'view_balances': "📊 عرض الأرصدة",
        'transaction_history': "📜 تاريخ المعاملات",
        'clear_balance': "✅ تسوية الرصيد",
        'delete_contact': "🗑️ حذف جهة اتصال",
        'language': "🌐 اللغة",
        'back_to_menu': "🔙 العودة للقائمة",
        'cancel': "❌ إلغاء",
        'no_contacts': "📭 ليس لديك أي جهات اتصال بعد!\nأضف جهة اتصال أولاً للمتابعة.",
        'no_contacts_delete': "📭 ليس لديك أي جهات اتصال لحذفها!",
        'add_contact_first': "👤 أضف جهة اتصال أولاً",
        'who_lent_to': "↗️ لمن أقرضت المال؟",
        'who_borrowed_from': "↙️ ممن استدنت المال؟",
        'clear_balance_with': "✅ تسوية الرصيد مع من؟",
        'view_history_with': "📜 عرض التاريخ مع من؟",
        'contact_not_found': "❌ جهة الاتصال غير موجودة!",
        'how_much_lent': "↗️ كم أقرضت لـ **{}**؟",
        'how_much_borrowed': "↙️ كم استدنت من **{}**؟",
        'how_much_paid': "✅ كم دفعت لـ **{}**؟",
        'enter_amount_hint': "\n\n💡 أرسل الرقم فقط (مثال: 1000)",
        'invalid_amount': "❌ يرجى إدخال رقم صحيح موجب (مثال: 1000)",
        'you_lent': "↗️ أقرضت **{:,.0f} دج** لـ **{}**",
        'you_borrowed': "↙️ استدنت **{:,.0f} دج** من **{}**",
        'you_paid': "✅ دفعت **{:,.0f} دج** لـ **{}**",
        'add_note_question': "\n\nهل تريد إضافة ملاحظة؟",
        'save_no_note': "💾 حفظ (بدون ملاحظة)",
        'add_note': "📝 إضافة ملاحظة",
        'transaction_recorded': "**تم تسجيل المعاملة!**",
        'lent_to': "أقرضت لـ",
        'borrowed_from': "استدنت من",
        'paid_to': "دفعت لـ",
        'settled': "🎉 أنت و **{}** متصالحان الآن!",
        'owes_you': "↗️ **{}** مدين لك بـ **{:,.0f} {}**",
        'you_owe': "↙️ أنت مدين لـ **{}** بـ **{:,.0f} {}**",
        'no_transactions': "📭 لم توجد معاملات مع **{}**",
        'history_with': "📜 **التاريخ مع {}:**",
        'you_lent_history': "أقرضت",
        'you_borrowed_history': "استدنت",
        'current_balance': "**الرصيد الحالي:**",
        'settled_balance': "✅ متصالح",
        'your_balances': "📊 **أرصدتك:**",
        'total_balance': "💯 **الرصيد الإجمالي:**",
        'net_positive': "💰 **الصافي: +{:,.0f} دج**\n_المطلوب لك أكثر مما عليك_",
        'net_negative': "❌ **الصافي: {:,.0f} دج**\n_المطلوب عليك أكثر مما لك_",
        'net_zero': "✅ **الصافي: 0 دج**\n_جميع الأرصدة متصالحة_",
        'delete_contact_title': "🗑️ **حذف جهة اتصال**\n\n⚠️ اختر جهة اتصال للحذف.\nسيؤدي هذا لحذف تاريخ المعاملات أيضاً!",
        'delete_confirmation': "🗑️ **حذف جهة اتصال**\n\nهل أنت متأكد من حذف **{}**؟{}\n\nلا يمكن التراجع عن هذا الإجراء!",
        'warning_owes_you': "\n⚠️ **تحذير:** {} مدين لك بـ {:,.0f} {}!",
        'warning_you_owe': "\n⚠️ **تحذير:** أنت مدين لـ {} بـ {:,.0f} {}!",
        'delete_success': "✅ تم حذف **{}**!\n\nتم حذف جميع تاريخ المعاملات.",
        'delete_failed': "❌ فشل في حذف **{}**.",
        'add_new_contact': "👤 **إضافة جهة اتصال جديدة**\n\nأرسل لي اسم جهة الاتصال:\n\n💡 مثال: أحمد بن علي",
        'name_too_short': "❌ الاسم يجب أن يكون حرفين على الأقل",
        'contact_added': "✅ تمت إضافة **{}** لجهات اتصالك!",
        'send_note': "📝 أرسل لي ملاحظة لهذه المعاملة:\n\n💡 مثال: فلوس غداء، أجرة تاكسي، إلخ",
        'choose_language': "🌐 **Choose Language / اختر اللغة**",
        'owes_short': "(مدين {:,.0f})",
        'you_owe_short': "(مدين عليك {:,.0f})",
        'analytics': "📊 الإحصائيات",
        'total_users': "👥 إجمالي المستخدمين: {}",
        'active_today': "🔥 نشطون اليوم: {}",
        'new_users_today': "🆕 مستخدمون جدد اليوم: {}",
        'total_transactions': "💼 إجمالي المعاملات: {}",
        'total_chats': "💬 إجمالي المحادثات: {}",
        'language_stats': "🌐 توزيع اللغات:",
        'analytics_summary': "📊 **إحصائيات البوت**\n\n{}\n{}\n{}\n{}\n{}\n\n{}\n{}",
        'group_mode': "👥 وضع المجموعة: البيانات منفصلة لكل محادثة",
        'private_mode': "👤 الوضع الخاص: البيانات الشخصية فقط"
    }
}

def get_user_language(user_id: int) -> str:
    """Get user's preferred language, default to English"""
    # For now, we'll store in memory. In production, store in database
    return user_languages.get(user_id, 'en')

def set_user_language(user_id: int, language: str):
    """Set user's preferred language"""
    user_languages[user_id] = language

def t(user_id: int, key: str, *args) -> str:
    """Translate text for user"""
    lang = get_user_language(user_id)
    text = TRANSLATIONS[lang].get(key, TRANSLATIONS['en'][key])
    if args:
        return text.format(*args)
    return text

# Global dictionary to store user language preferences
user_languages = {}

class MarkilyBot:
    def __init__(self, bot_token: str, db_base_path: str = "/app/data"):
        self.bot_token = bot_token
        self.db_base_path = db_base_path
        # Only create directory if it's not the current directory
        if self.db_base_path and self.db_base_path != ".":
            os.makedirs(self.db_base_path, exist_ok=True)
        # Initialize analytics database (shared across all chats)
        self.init_analytics_database()
    
    def get_db_path(self, chat_id: int) -> str:
        """Get database path for specific chat"""
        if self.db_base_path and self.db_base_path != ".":
            return os.path.join(self.db_base_path, f"markily_chat_{chat_id}.db")
        return f"markily_chat_{chat_id}.db"
    
    def get_analytics_db_path(self) -> str:
        """Get analytics database path"""
        if self.db_base_path and self.db_base_path != ".":
            return os.path.join(self.db_base_path, "markily_analytics.db")
        return "markily_analytics.db"
    
    def init_analytics_database(self):
        """Initialize analytics database for tracking user statistics"""
        conn = sqlite3.connect(self.get_analytics_db_path())
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_analytics (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_commands INTEGER DEFAULT 0,
                total_transactions INTEGER DEFAULT 0,
                language_preference TEXT DEFAULT 'en'
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_analytics (
                chat_id INTEGER PRIMARY KEY,
                chat_type TEXT,
                chat_title TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_users INTEGER DEFAULT 0,
                total_transactions INTEGER DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_stats (
                date TEXT PRIMARY KEY,
                active_users INTEGER DEFAULT 0,
                new_users INTEGER DEFAULT 0,
                total_transactions INTEGER DEFAULT 0,
                total_commands INTEGER DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def init_database(self, chat_id: int):
        """Initialize database for specific chat"""
        db_path = self.get_db_path(chat_id)
        conn = sqlite3.connect(db_path)
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
    
    def track_user_activity(self, user_id: int, username: str = None, first_name: str = None, 
                           last_name: str = None, command_type: str = "command"):
        """Track user activity for analytics"""
        conn = sqlite3.connect(self.get_analytics_db_path())
        cursor = conn.cursor()
        
        # Update or insert user analytics
        cursor.execute('''
            INSERT OR REPLACE INTO user_analytics 
            (user_id, username, first_name, last_name, first_seen, last_seen, total_commands, total_transactions, language_preference)
            VALUES (?, ?, ?, ?, 
                    COALESCE((SELECT first_seen FROM user_analytics WHERE user_id = ?), CURRENT_TIMESTAMP),
                    CURRENT_TIMESTAMP,
                    COALESCE((SELECT total_commands FROM user_analytics WHERE user_id = ?), 0) + ?,
                    COALESCE((SELECT total_transactions FROM user_analytics WHERE user_id = ?), 0) + ?,
                    COALESCE((SELECT language_preference FROM user_analytics WHERE user_id = ?), 'en'))
        ''', (user_id, username, first_name, last_name, user_id, user_id, 
              1 if command_type == "command" else 0, user_id, 
              1 if command_type == "transaction" else 0, user_id))
        
        # Update daily stats
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('''
            INSERT OR REPLACE INTO daily_stats 
            (date, active_users, new_users, total_transactions, total_commands)
            VALUES (?, 
                    (SELECT COUNT(DISTINCT user_id) FROM user_analytics WHERE DATE(last_seen) = ?),
                    (SELECT COUNT(*) FROM user_analytics WHERE DATE(first_seen) = ?),
                    COALESCE((SELECT total_transactions FROM daily_stats WHERE date = ?), 0) + ?,
                    COALESCE((SELECT total_commands FROM daily_stats WHERE date = ?), 0) + ?)
        ''', (today, today, today, today, 
              1 if command_type == "transaction" else 0, today,
              1 if command_type == "command" else 0))
        
        conn.commit()
        conn.close()
    
    def track_chat_activity(self, chat_id: int, chat_type: str, chat_title: str = None):
        """Track chat activity for analytics"""
        conn = sqlite3.connect(self.get_analytics_db_path())
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO chat_analytics 
            (chat_id, chat_type, chat_title, created_at, last_activity, total_users, total_transactions)
            VALUES (?, ?, ?, 
                    COALESCE((SELECT created_at FROM chat_analytics WHERE chat_id = ?), CURRENT_TIMESTAMP),
                    CURRENT_TIMESTAMP,
                    COALESCE((SELECT total_users FROM chat_analytics WHERE chat_id = ?), 0),
                    COALESCE((SELECT total_transactions FROM chat_analytics WHERE chat_id = ?), 0))
        ''', (chat_id, chat_type, chat_title, chat_id, chat_id, chat_id))
        
        conn.commit()
        conn.close()
    
    def get_analytics_summary(self) -> dict:
        """Get analytics summary"""
        conn = sqlite3.connect(self.get_analytics_db_path())
        cursor = conn.cursor()
        
        # Total users
        cursor.execute('SELECT COUNT(*) FROM user_analytics')
        total_users = cursor.fetchone()[0]
        
        # Active users today
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('SELECT COUNT(*) FROM user_analytics WHERE DATE(last_seen) = ?', (today,))
        active_today = cursor.fetchone()[0]
        
        # New users today
        cursor.execute('SELECT COUNT(*) FROM user_analytics WHERE DATE(first_seen) = ?', (today,))
        new_today = cursor.fetchone()[0]
        
        # Total transactions
        cursor.execute('SELECT SUM(total_transactions) FROM user_analytics')
        total_transactions = cursor.fetchone()[0] or 0
        
        # Total chats
        cursor.execute('SELECT COUNT(*) FROM chat_analytics')
        total_chats = cursor.fetchone()[0]
        
        # Language distribution
        cursor.execute('SELECT language_preference, COUNT(*) FROM user_analytics GROUP BY language_preference')
        language_stats = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            'total_users': total_users,
            'active_today': active_today,
            'new_today': new_today,
            'total_transactions': total_transactions,
            'total_chats': total_chats,
            'language_stats': language_stats
        }
    
    def get_user_contacts(self, user_id: int, chat_id: int) -> List[Tuple]:
        db_path = self.get_db_path(chat_id)
        conn = sqlite3.connect(db_path)
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
    
    def search_contact(self, user_id: int, search_term: str, chat_id: int) -> Optional[Tuple]:
        contacts = self.get_user_contacts(user_id, chat_id)
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
    
    def add_contact(self, user_id: int, name: str, chat_id: int, phone: str = None, telegram_username: str = None) -> int:
        db_path = self.get_db_path(chat_id)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO contacts (user_id, name, phone, telegram_username)
            VALUES (?, ?, ?, ?)
        ''', (user_id, name, phone, telegram_username))
        contact_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return contact_id
    
    def delete_contact(self, user_id: int, contact_id: int, chat_id: int) -> bool:
        db_path = self.get_db_path(chat_id)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM transactions WHERE user_id = ? AND contact_id = ?', (user_id, contact_id))
        cursor.execute('DELETE FROM contacts WHERE user_id = ? AND id = ?', (user_id, contact_id))
        
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted
    
    def add_transaction(self, user_id: int, contact_id: int, amount: float, 
                       currency: str, transaction_type: str, chat_id: int, note: str = None) -> int:
        db_path = self.get_db_path(chat_id)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO transactions (user_id, contact_id, amount, currency, transaction_type, note)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, contact_id, amount, currency, transaction_type, note))
        transaction_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Track transaction for analytics
        self.track_user_activity(user_id, command_type="transaction")
        
        return transaction_id
    
    def get_balance(self, user_id: int, contact_id: int, chat_id: int) -> Tuple[float, str]:
        db_path = self.get_db_path(chat_id)
        conn = sqlite3.connect(db_path)
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
    
    def get_total_balance(self, user_id: int, chat_id: int) -> Tuple[float, float, float]:
        db_path = self.get_db_path(chat_id)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT c.id FROM contacts c WHERE c.user_id = ?
        ''', (user_id,))
        
        contacts = cursor.fetchall()
        conn.close()
        
        total_owed_to_me = 0.0
        total_i_owe = 0.0
        
        for contact in contacts:
            contact_id = contact[0]
            balance, _ = self.get_balance(user_id, contact_id, chat_id)
            
            if balance > 0:
                total_owed_to_me += balance
            elif balance < 0:
                total_i_owe += abs(balance)
        
        net_balance = total_owed_to_me - total_i_owe
        
        return total_owed_to_me, total_i_owe, net_balance
    
    def get_transaction_history(self, user_id: int, contact_id: int, chat_id: int) -> List[Tuple]:
        db_path = self.get_db_path(chat_id)
        conn = sqlite3.connect(db_path)
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
    
    def register_user(self, user_id: int, chat_id: int, username: str = None, 
                     first_name: str = None, last_name: str = None):
        # Initialize database for this chat if it doesn't exist
        self.init_database(chat_id)
        
        db_path = self.get_db_path(chat_id)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO users (telegram_id, username, first_name, last_name)
            VALUES (?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name))
        conn.commit()
        conn.close()
        
        # Track user activity for analytics
        self.track_user_activity(user_id, username, first_name, last_name)

bot = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    
    # Register user and track chat activity
    bot.register_user(user.id, chat.id, user.username, user.first_name, user.last_name)
    bot.track_chat_activity(chat.id, chat.type, getattr(chat, 'title', None))
    
    # Track command activity
    bot.track_user_activity(user.id, user.username, user.first_name, user.last_name, "command")
    
    keyboard = [
        [
            InlineKeyboardButton(t(user.id, 'lent_money'), callback_data="action_lend"),
            InlineKeyboardButton(t(user.id, 'borrowed_money'), callback_data="action_borrow")
        ],
        [
            InlineKeyboardButton(t(user.id, 'add_contact'), callback_data="action_add_contact"),
            InlineKeyboardButton(t(user.id, 'view_balances'), callback_data="action_balances")
        ],
        [
            InlineKeyboardButton(t(user.id, 'transaction_history'), callback_data="action_history"),
            InlineKeyboardButton(t(user.id, 'clear_balance'), callback_data="action_clear")
        ],
        [
            InlineKeyboardButton(t(user.id, 'delete_contact'), callback_data="action_delete_contact"),
            InlineKeyboardButton(t(user.id, 'language'), callback_data="action_language")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = t(user.id, 'welcome', user.first_name)
    
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.callback_query.edit_message_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_language_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [
            InlineKeyboardButton("🇺🇸 English", callback_data="set_language_en"),
            InlineKeyboardButton("🇩🇿 العربية", callback_data="set_language_ar")
        ],
        [
            InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        t(query.from_user.id, 'choose_language'),
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    language = query.data.split('_')[2]  # set_language_en -> en
    set_user_language(query.from_user.id, language)
    
    await start(update, context)

async def show_contacts_for_action(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str):
    query = update.callback_query
    await query.answer()
    
    chat_id = query.message.chat.id
    contacts = bot.get_user_contacts(query.from_user.id, chat_id)
    
    if not contacts:
        keyboard = [
            [InlineKeyboardButton(t(query.from_user.id, 'add_contact_first'), callback_data="action_add_contact")],
            [InlineKeyboardButton(t(query.from_user.id, 'back_to_menu'), callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            t(query.from_user.id, 'no_contacts'),
            reply_markup=reply_markup
        )
        return
    
    keyboard = []
    for contact in contacts:
        contact_id, name, phone, telegram_username = contact
        balance, currency = bot.get_balance(query.from_user.id, contact_id, chat_id)
        
        status = ""
        if balance > 0:
            status = f" ↗️{t(query.from_user.id, 'owes_short', balance)}"
        elif balance < 0:
            status = f" ↙️{t(query.from_user.id, 'you_owe_short', abs(balance))}"
        
        button_text = f"{name}{status}"
        callback_data = f"{action}_{contact_id}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
    
    keyboard.append([InlineKeyboardButton(t(query.from_user.id, 'back_to_menu'), callback_data="back_to_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    action_text = {
        "lend": t(query.from_user.id, 'who_lent_to'),
        "borrow": t(query.from_user.id, 'who_borrowed_from'),
        "clear": t(query.from_user.id, 'clear_balance_with'),
        "history": t(query.from_user.id, 'view_history_with')
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
    context.user_data['chat_id'] = query.message.chat.id
    
    chat_id = query.message.chat.id
    contact = next((c for c in bot.get_user_contacts(query.from_user.id, chat_id) if c[0] == int(contact_id)), None)
    if not contact:
        await query.edit_message_text(t(query.from_user.id, 'contact_not_found'))
        return ConversationHandler.END
    
    context.user_data['contact_name'] = contact[1]
    
    if action == "history":
        await show_transaction_history(update, context)
        return ConversationHandler.END
    
    action_text = {
        "lend": t(query.from_user.id, 'how_much_lent', contact[1]),
        "borrow": t(query.from_user.id, 'how_much_borrowed', contact[1]),
        "clear": t(query.from_user.id, 'how_much_paid', contact[1])
    }
    
    keyboard = [[InlineKeyboardButton(t(query.from_user.id, 'cancel'), callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"{action_text.get(action, 'Enter amount:')}{t(query.from_user.id, 'enter_amount_hint')}",
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
        await update.message.reply_text(t(update.effective_user.id, 'invalid_amount'))
        return WAITING_FOR_AMOUNT
    
    context.user_data['amount'] = amount
    action = context.user_data['action']
    contact_name = context.user_data['contact_name']
    
    action_text = {
        "lend": t(update.effective_user.id, 'you_lent', amount, contact_name),
        "borrow": t(update.effective_user.id, 'you_borrowed', amount, contact_name),
        "clear": t(update.effective_user.id, 'you_paid', amount, contact_name)
    }
    
    keyboard = [
        [
            InlineKeyboardButton(t(update.effective_user.id, 'save_no_note'), callback_data="save_transaction_no_note"),
            InlineKeyboardButton(t(update.effective_user.id, 'add_note'), callback_data="add_note")
        ],
        [InlineKeyboardButton(t(update.effective_user.id, 'cancel'), callback_data="back_to_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"{action_text.get(action, '')}{t(update.effective_user.id, 'add_note_question')}",
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
    chat_id = context.user_data.get('chat_id') or update.effective_chat.id
    
    user_id = update.effective_user.id
    
    if action == "clear":
        current_balance, _ = bot.get_balance(user_id, contact_id, chat_id)
        transaction_type = 'borrow' if current_balance > 0 else 'lend'
    else:
        transaction_type = action
    
    bot.add_transaction(user_id, contact_id, amount, 'DZD', transaction_type, chat_id, note)
    
    balance, currency = bot.get_balance(user_id, contact_id, chat_id)
    
    note_text = f" ({note})" if note else ""
    
    action_emoji = {"lend": "↗️", "borrow": "↙️", "clear": "✅"}
    action_verb = {
        "lend": t(user_id, 'lent_to'), 
        "borrow": t(user_id, 'borrowed_from'), 
        "clear": t(user_id, 'paid_to')
    }
    
    message = f"{action_emoji.get(action, '')} {t(user_id, 'transaction_recorded')}\n\n"
    message += f"{action_verb.get(action, '')} **{contact_name}**: {amount:,.0f} DZD{note_text}\n\n"
    
    if abs(balance) < 0.01:
        message += t(user_id, 'settled', contact_name)
    elif balance > 0:
        message += t(user_id, 'owes_you', contact_name, balance, currency)
    else:
        message += t(user_id, 'you_owe', contact_name, abs(balance), currency)
    
    keyboard = [[InlineKeyboardButton(t(user_id, 'back_to_menu'), callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def show_transaction_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    contact_id = context.user_data['contact_id']
    contact_name = context.user_data['contact_name']
    chat_id = context.user_data.get('chat_id') or query.message.chat.id
    user_id = update.effective_user.id
    
    history = bot.get_transaction_history(user_id, contact_id, chat_id)
    
    if not history:
        message = t(user_id, 'no_transactions', contact_name)
    else:
        message = f"� **History with {contact_name}:**\n\n"
        
        for amount, currency, transaction_type, note, created_at in history[:10]:
            date = datetime.fromisoformat(created_at).strftime("%m/%d")
            
            if transaction_type == 'lend':
                emoji = "↗️"
                action = t(user_id, 'you_lent_history')
            else:
                emoji = "↙️" 
                action = t(user_id, 'you_borrowed_history')
            
            note_text = f" - {note}" if note else ""
            message += f"{emoji} {action} {amount:,.0f} {currency}{note_text} ({date})\n"
        
        balance, currency = bot.get_balance(user_id, contact_id, chat_id)
        message += f"\n{t(user_id, 'current_balance')}\n"
        if balance > 0:
            message += t(user_id, 'owes_you', contact_name, balance, currency)
        elif balance < 0:
            message += t(user_id, 'you_owe', contact_name, abs(balance), currency)
        else:
            message += t(user_id, 'settled_balance')
    
    keyboard = [[InlineKeyboardButton(t(user_id, 'back_to_menu'), callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def show_all_balances(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    chat_id = query.message.chat.id
    
    contacts = bot.get_user_contacts(user_id, chat_id)
    
    if not contacts:
        keyboard = [
            [InlineKeyboardButton(t(user_id, 'add_contact'), callback_data="action_add_contact")],
            [InlineKeyboardButton(t(user_id, 'back_to_menu'), callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            t(user_id, 'no_contacts'),
            reply_markup=reply_markup
        )
        return
    
    message = t(user_id, 'your_balances') + "\n\n"
    
    for contact in contacts:
        contact_id, name, phone, telegram_username = contact
        balance, currency = bot.get_balance(user_id, contact_id, chat_id)
        
        if balance > 0:
            message += f"↗️ **{name}** owes you **{balance:,.0f} {currency}**\n"
        elif balance < 0:
            message += f"↙️ You owe **{name}** **{abs(balance):,.0f} {currency}**\n"
        else:
            message += f"✅ **{name}** - settled\n"
    
    # Add total balance summary
    total_owed_to_me, total_i_owe, net_balance = bot.get_total_balance(user_id, chat_id)
    message += "\n" + "─" * 25 + "\n"
    message += t(user_id, 'total_balance') + "\n"
    if net_balance > 0:
        message += t(user_id, 'net_positive', net_balance)
    elif net_balance < 0:
        message += t(user_id, 'net_negative', net_balance)
    else:
        message += t(user_id, 'net_zero')
    
    keyboard = [[InlineKeyboardButton(t(user_id, 'back_to_menu'), callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def show_contacts_for_deletion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    chat_id = query.message.chat.id
    
    contacts = bot.get_user_contacts(user_id, chat_id)
    
    if not contacts:
        keyboard = [
            [InlineKeyboardButton(t(user_id, 'add_contact_first'), callback_data="action_add_contact")],
            [InlineKeyboardButton(t(user_id, 'back_to_menu'), callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            t(user_id, 'no_contacts_delete'),
            reply_markup=reply_markup
        )
        return
    
    keyboard = []
    for contact in contacts:
        contact_id, name, phone, telegram_username = contact
        balance, currency = bot.get_balance(user_id, contact_id, chat_id)
        
        status = ""
        if balance > 0:
            status = f" 💰{t(user_id, 'owes_short', balance)}"
        elif balance < 0:
            status = f" 💸{t(user_id, 'you_owe_short', abs(balance))}"
        
        button_text = f"🗑️ {name}{status}"
        callback_data = f"delete_{contact_id}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
    
    keyboard.append([InlineKeyboardButton(t(user_id, 'back_to_menu'), callback_data="back_to_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        t(user_id, 'delete_contact_title'),
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def confirm_delete_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    chat_id = query.message.chat.id
    
    contact_id = int(query.data.split('_')[1])
    
    contact = next((c for c in bot.get_user_contacts(user_id, chat_id) if c[0] == contact_id), None)
    if not contact:
        await query.edit_message_text(t(user_id, 'contact_not_found'))
        return
    
    contact_name = contact[1]
    balance, currency = bot.get_balance(user_id, contact_id, chat_id)
    
    balance_warning = ""
    if balance != 0:
        if balance > 0:
            balance_warning = t(user_id, 'warning_owes_you', contact_name, balance, currency)
        else:
            balance_warning = t(user_id, 'warning_you_owe', contact_name, abs(balance), currency)
    
    keyboard = [
        [
            InlineKeyboardButton(t(user_id, 'cancel'), callback_data="action_delete_contact"),
            InlineKeyboardButton("🗑️ Delete", callback_data=f"confirm_delete_{contact_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        t(user_id, 'delete_confirmation', contact_name, balance_warning),
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def delete_contact_confirmed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    chat_id = query.message.chat.id
    
    contact_id = int(query.data.split('_')[2])
    
    contact = next((c for c in bot.get_user_contacts(user_id, chat_id) if c[0] == contact_id), None)
    if not contact:
        await query.edit_message_text(t(user_id, 'contact_not_found'))
        return
    
    contact_name = contact[1]
    
    success = bot.delete_contact(user_id, contact_id, chat_id)
    
    if success:
        message = t(user_id, 'delete_success', contact_name)
    else:
        message = t(user_id, 'delete_failed', contact_name)
    
    keyboard = [[InlineKeyboardButton(t(user_id, 'back_to_menu'), callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def start_add_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    keyboard = [[InlineKeyboardButton(t(user_id, 'cancel'), callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        t(user_id, 'add_new_contact'),
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return WAITING_FOR_CONTACT_NAME

async def show_analytics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bot analytics (admin only)"""
    user_id = update.effective_user.id
    
    # Admin check - only these users can see analytics
    ADMIN_IDS = [2133241990]  
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Access denied - Admin only")
        return
    
    stats = bot.get_analytics_summary()
    
    total_users_text = t(user_id, 'total_users', stats['total_users'])
    active_today_text = t(user_id, 'active_today', stats['active_today'])
    new_today_text = t(user_id, 'new_users_today', stats['new_today'])
    total_transactions_text = t(user_id, 'total_transactions', stats['total_transactions'])
    total_chats_text = t(user_id, 'total_chats', stats['total_chats'])
    
    lang_stats_text = t(user_id, 'language_stats')
    for lang, count in stats['language_stats'].items():
        lang_name = "English" if lang == 'en' else "العربية"
        lang_stats_text += f"\n  • {lang_name}: {count}"
    
    mode_text = t(user_id, 'group_mode') if update.effective_chat.type != 'private' else t(user_id, 'private_mode')
    
    message = t(user_id, 'analytics_summary', 
                total_users_text, active_today_text, new_today_text, 
                total_transactions_text, total_chats_text,
                lang_stats_text, mode_text)
    
    if update.message:
        await update.message.reply_text(message, parse_mode='Markdown')
    else:
        await update.callback_query.edit_message_text(message, parse_mode='Markdown')

async def get_my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Helper command to get your user ID for analytics setup"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "No username"
    first_name = update.effective_user.first_name or "No name"
    
    message = f"🆔 **Your Telegram Info:**\n\n"
    message += f"**User ID:** `{user_id}`\n"
    message += f"**Username:** @{username}\n" 
    message += f"**Name:** {first_name}\n\n"
    message += f"💡 Copy your User ID (`{user_id}`) and replace `123456789` in the ADMIN_IDS list in your bot code to enable analytics access."
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def handle_contact_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    if len(name) < 2:
        await update.message.reply_text(t(user_id, 'name_too_short'))
        return WAITING_FOR_CONTACT_NAME
    
    contact_id = bot.add_contact(user_id, name, chat_id)
    
    keyboard = [[InlineKeyboardButton(t(user_id, 'back_to_menu'), callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        t(user_id, 'contact_added', name),
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
    
    elif data == "action_delete_contact":
        await show_contacts_for_deletion(update, context)
        return ConversationHandler.END
    
    elif data == "action_language":
        await show_language_selection(update, context)
        return ConversationHandler.END
    
    elif data.startswith("set_language_"):
        await set_language(update, context)
        return ConversationHandler.END
    
    elif data.startswith("delete_") and not data.startswith("confirm_delete_"):
        await confirm_delete_contact(update, context)
        return ConversationHandler.END
    
    elif data.startswith("confirm_delete_"):
        await delete_contact_confirmed(update, context)
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
        user_id = query.from_user.id
        keyboard = [[InlineKeyboardButton(t(user_id, 'cancel'), callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            t(user_id, 'send_note'),
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
    
    # Use local database path when not in Docker
    db_base_path = "/app/data" if os.path.exists("/app") else "."
    bot = MarkilyBot(BOT_TOKEN, db_base_path)
    
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
    application.add_handler(CommandHandler("analytics", show_analytics))
    application.add_handler(CommandHandler("myid", get_my_id))
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(button_callback))
    
    print("🚀 Markily Bot is starting...")
    print("📊 Analytics tracking enabled")
    print("👥 Group support enabled - separate data per chat")
    print("💾 Database structure: chat-specific databases")
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
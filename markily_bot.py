import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
import re
import os
from difflib import get_close_matches
from dotenv import load_dotenv
import io
import asyncio
from dateutil import parser as date_parser
from dateutil.relativedelta import relativedelta
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import urllib.request

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

WAITING_FOR_CONTACT_NAME, WAITING_FOR_AMOUNT, WAITING_FOR_NOTE, WAITING_FOR_REMINDER_CONTACT, WAITING_FOR_REMINDER_DATETIME, WAITING_FOR_REMINDER_TIME, WAITING_FOR_REMINDER_NOTE = range(7)

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
        'private_mode': "👤 Private Mode: Personal data only",
        'export_pdf': "📄 Export PDF",
        'generating_pdf': "📄 Generating PDF report...",
        'pdf_generated': "✅ **PDF Report Generated!**\n\n📄 Transaction history with **{}**\n📅 Generated: {}",
        'pdf_error': "❌ Error generating PDF report. Please try again.",
        'no_transactions_pdf': "📭 No transactions found with **{}** to export.",
        'pdf_title': "Transaction History Report",
        'pdf_subtitle': "Debt & Loan Statement",
        'pdf_contact': "Contact: {}",
        'pdf_period': "Period: {} to {}",
        'pdf_date': "Date",
        'pdf_description': "Description",
        'pdf_amount': "Amount (DZD)",
        'pdf_balance': "Balance (DZD)",
        'pdf_final_balance': "Final Balance",
        'pdf_you_lent': "You lent",
        'pdf_you_borrowed': "You borrowed",
        'pdf_payment': "Payment received",
        'pdf_summary': "Summary",
        'pdf_total_lent': "Total Lent:",
        'pdf_total_borrowed': "Total Borrowed:", 
        'pdf_net_balance': "Net Balance:",
        'pdf_footer': "Generated by Markily Bot on {}",
        'set_reminder': "⏰ Set Reminder",
        'view_reminders': "📅 View Reminders",
        'reminder_for_whom': "⏰ Set reminder for whom?",
        'reminder_date_time': "📅 When should I remind you?\n\nChoose a quick option or send custom date:",
        'today': "📅 Today",
        'tomorrow': "📅 Tomorrow", 
        'this_weekend': "📅 This Weekend",
        'next_week': "📅 Next Week",
        'next_monday': "📅 Next Monday",
        'custom_date': "📝 Custom Date",
        'select_time': "⏰ Select time for {}:",
        'morning_9am': "🌅 9:00 AM",
        'morning_10am': "☀️ 10:00 AM", 
        'afternoon_2pm': "🌞 2:00 PM",
        'afternoon_5pm': "🌇 5:00 PM",
        'evening_8pm': "🌙 8:00 PM",
        'custom_time': "⏰ Custom Time",
        'reminder_note': "📝 What should I remind you about?\n\n💡 Example: Payment due, Collect money, etc.",
        'invalid_datetime': "❌ Invalid date/time format. Please try again.\n\n💡 Examples:\n• Aug 27 10AM\n• 2025-08-27 10:00\n• Tomorrow 2PM\n• Next Monday 9AM",
        'reminder_set': "✅ **Reminder Set!**\n\n⏰ **When:** {}\n👤 **Contact:** {}\n📝 **Note:** {}\n\nI'll remind you at the specified time!",
        'no_reminders': "📅 You don't have any reminders set.",
        'your_reminders': "📅 **Your Reminders:**",
        'reminder_due': "⏰ **REMINDER** ⏰\n\n👤 **Contact:** {}\n📝 **Note:** {}\n📅 **Time:** {}\n\n💰 Current balance: {}",
        'reminder_deleted': "✅ Reminder deleted!",
        'delete_reminder': "🗑️ Delete"
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
        'private_mode': "👤 الوضع الخاص: البيانات الشخصية فقط",
        'export_pdf': "📄 تصدير PDF",
        'generating_pdf': "📄 جاري إنشاء تقرير PDF...",
        'pdf_generated': "✅ **تم إنشاء تقرير PDF!**\n\n📄 تاريخ المعاملات مع **{}**\n📅 تاريخ الإنشاء: {}",
        'pdf_error': "❌ خطأ في إنشاء تقرير PDF. حاول مرة أخرى.",
        'no_transactions_pdf': "📭 لم توجد معاملات مع **{}** للتصدير.",
        'pdf_title': "تقرير تاريخ المعاملات",
        'pdf_subtitle': "كشف الديون والقروض",
        'pdf_contact': "جهة الاتصال: {}",
        'pdf_period': "الفترة: {} إلى {}",
        'pdf_date': "التاريخ",
        'pdf_description': "الوصف",
        'pdf_amount': "المبلغ (دج)",
        'pdf_balance': "الرصيد (دج)",
        'pdf_final_balance': "الرصيد النهائي",
        'pdf_you_lent': "أقرضت",
        'pdf_you_borrowed': "استدنت",
        'pdf_payment': "دفعة مستلمة",
        'pdf_summary': "الملخص",
        'pdf_total_lent': "إجمالي المُقرض:",
        'pdf_total_borrowed': "إجمالي المُستدان:",
        'pdf_net_balance': "الرصيد الصافي:",
        'pdf_footer': "تم الإنشاء بواسطة بوت Markily في {}",
        'set_reminder': "⏰ تعيين تذكير",
        'view_reminders': "📅 عرض التذكيرات",
        'reminder_for_whom': "⏰ تعيين تذكير لمن؟",
        'reminder_date_time': "📅 متى يجب أن أذكرك؟\n\nاختر خيار سريع أو أرسل تاريخ مخصص:",
        'today': "📅 اليوم",
        'tomorrow': "📅 غداً",
        'this_weekend': "📅 نهاية الأسبوع",
        'next_week': "📅 الأسبوع القادم",
        'next_monday': "📅 الاثنين القادم",
        'custom_date': "📝 تاريخ مخصص",
        'select_time': "⏰ اختر الوقت لـ {}:",
        'morning_9am': "🌅 9:00 صباحاً",
        'morning_10am': "☀️ 10:00 صباحاً",
        'afternoon_2pm': "🌞 2:00 ظهراً",
        'afternoon_5pm': "🌇 5:00 مساءً",
        'evening_8pm': "🌙 8:00 مساءً",
        'custom_time': "⏰ وقت مخصص",
        'reminder_note': "📝 بماذا يجب أن أذكرك؟\n\n💡 مثال: موعد السداد، تحصيل المال، إلخ",
        'invalid_datetime': "❌ صيغة التاريخ/الوقت غير صحيحة. حاول مرة أخرى.\n\n💡 أمثلة:\n• 27 أغسطس 10 صباحاً\n• 2025-08-27 10:00\n• غداً 2 ظهراً\n• الاثنين القادم 9 صباحاً",
        'reminder_set': "✅ **تم تعيين التذكير!**\n\n⏰ **متى:** {}\n👤 **جهة الاتصال:** {}\n📝 **ملاحظة:** {}\n\nسأذكرك في الوقت المحدد!",
        'no_reminders': "📅 ليس لديك أي تذكيرات محددة.",
        'your_reminders': "📅 **تذكيراتك:**",
        'reminder_due': "⏰ **تذكير** ⏰\n\n👤 **جهة الاتصال:** {}\n📝 **ملاحظة:** {}\n📅 **الوقت:** {}\n\n💰 الرصيد الحالي: {}",
        'reminder_deleted': "✅ تم حذف التذكير!",
        'delete_reminder': "🗑️ حذف"
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
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                contact_id INTEGER,
                reminder_datetime TIMESTAMP NOT NULL,
                note TEXT,
                is_active BOOLEAN DEFAULT 1,
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
    
    def generate_pdf_report(self, user_id: int, contact_id: int, chat_id: int, user_name: str = "User") -> Optional[bytes]:
        """Generate simplified PDF report with Arabic support and Markily logo"""
        try:
            logger.info(f"Starting PDF generation for user {user_id}, contact {contact_id}, chat {chat_id}")
            
            # Ensure database is properly initialized
            self.init_database(chat_id)
            
            # Get transaction history and contact info
            history = self.get_transaction_history(user_id, contact_id, chat_id)
            if not history:
                logger.warning(f"No transaction history found for user {user_id}, contact {contact_id}")
                return None
                
            contacts = self.get_user_contacts(user_id, chat_id)
            contact = next((c for c in contacts if c[0] == contact_id), None)
            if not contact:
                logger.warning(f"Contact {contact_id} not found for user {user_id}")
                return None
                
            contact_name = contact[1]
            lang = get_user_language(user_id)
            
            # Register Arabic font for proper text rendering
            try:
                # Try to register a system font that supports Arabic
                # On most systems, Arial Unicode MS or similar fonts support Arabic
                from reportlab.pdfbase import pdfmetrics
                from reportlab.pdfbase.ttfonts import TTFont
                
                # Try common system fonts that support Arabic
                arabic_font_candidates = [
                    '/System/Library/Fonts/Arial Unicode.ttf',  # macOS
                    '/System/Library/Fonts/Helvetica.ttc',     # macOS fallback
                    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',  # Linux
                    'C:\\Windows\\Fonts\\arial.ttf',           # Windows
                ]
                
                arabic_font_registered = False
                for font_path in arabic_font_candidates:
                    if os.path.exists(font_path):
                        try:
                            pdfmetrics.registerFont(TTFont('ArabicFont', font_path))
                            arabic_font_registered = True
                            logger.info(f"Registered Arabic font from {font_path}")
                            break
                        except Exception as font_error:
                            logger.warning(f"Failed to register font {font_path}: {font_error}")
                            continue
                            
                if not arabic_font_registered:
                    logger.warning("No Arabic font found, falling back to Helvetica")
                    
            except Exception as font_setup_error:
                logger.warning(f"Arabic font setup failed: {font_setup_error}")
                arabic_font_registered = False
            
            # Create PDF in memory
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, 
                                  rightMargin=2*cm, leftMargin=2*cm, 
                                  topMargin=2*cm, bottomMargin=2*cm)
            
            # Define styles
            styles = getSampleStyleSheet()
            
            # Arabic/RTL support
            is_arabic = lang == 'ar'
            alignment = TA_RIGHT if is_arabic else TA_LEFT
            title_alignment = TA_CENTER
            
            # Table alignment strings (ReportLab tables need string alignment)
            table_alignment = 'RIGHT' if is_arabic else 'LEFT'
            
            # Font selection based on Arabic support
            if is_arabic and arabic_font_registered:
                base_font = 'ArabicFont'
                bold_font = 'ArabicFont'  # Arabic font doesn't have bold variant
            else:
                base_font = 'Helvetica'
                bold_font = 'Helvetica-Bold'
            
            # Custom styles
            logo_style = ParagraphStyle('LogoStyle', alignment=TA_CENTER, spaceAfter=20)
            
            title_style = ParagraphStyle(
                'TitleStyle', fontSize=20, fontName=bold_font,
                alignment=title_alignment, spaceAfter=15,
                textColor=colors.HexColor('#011C1C')
            )
            
            subtitle_style = ParagraphStyle(
                'SubtitleStyle', fontSize=14, fontName=base_font,
                alignment=title_alignment, spaceAfter=20,
                textColor=colors.HexColor('#666666')
            )
            
            info_style = ParagraphStyle(
                'InfoStyle', fontSize=11, fontName=base_font,
                alignment=alignment, spaceAfter=8
            )
            
            header_style = ParagraphStyle(
                'HeaderStyle', fontSize=12, fontName=bold_font,
                alignment=alignment, spaceAfter=15,
                textColor=colors.HexColor('#011C1C')
            )
            
            # Build PDF content
            story = []
            
            # Add Markily Logo from file
            logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")
            try:
                if os.path.exists(logo_path):
                    logo = Image(logo_path, width=4*cm, height=2*cm)
                    logo.hAlign = 'CENTER'
                    story.append(logo)
                    story.append(Spacer(1, 15))
                    logger.info(f"Logo loaded successfully from {logo_path}")
                else:
                    logger.warning(f"Logo file not found at {logo_path}")
                    # Fallback to text logo if file doesn't exist
                    logo_text = "💰 MARKILY"
                    story.append(Paragraph(f'<font size="24" color="#011C1C"><b>{logo_text}</b></font>', logo_style))
                    story.append(Spacer(1, 10))
            except Exception as logo_error:
                logger.warning(f"Logo loading failed: {logo_error}")
                # Fallback to text logo
                logo_text = "💰 MARKILY"
                story.append(Paragraph(f'<font size="24" color="#011C1C"><b>{logo_text}</b></font>', logo_style))
                story.append(Spacer(1, 10))
            
            # Title - use safe translation approach
            try:
                if is_arabic:
                    title = t(user_id, 'pdf_title')
                    subtitle = t(user_id, 'pdf_subtitle') 
                else:
                    title = "Transaction Statement"
                    subtitle = "Debt & Payment Record"
            except Exception as trans_error:
                logger.warning(f"Translation error: {trans_error}")
                title = "Transaction Statement"
                subtitle = "Debt & Payment Record"
                
            story.append(Paragraph(title, title_style))
            story.append(Paragraph(subtitle, subtitle_style))
            
            # Divider line
            story.append(Spacer(1, 5))
            story.append(Paragraph('<hr width="100%" color="#5AD25B"/>', styles['Normal']))
            story.append(Spacer(1, 15))
            
            # Contact information
            contact_label = "جهة الاتصال:" if is_arabic else "Contact:"
            story.append(Paragraph(f'<b>{contact_label}</b> {contact_name}', info_style))
            
            # Date range
            if history:
                try:
                    first_date = datetime.fromisoformat(history[-1][4]).strftime("%Y/%m/%d")
                    last_date = datetime.fromisoformat(history[0][4]).strftime("%Y/%m/%d") 
                    date_label = "الفترة:" if is_arabic else "Period:"
                    story.append(Paragraph(f'<b>{date_label}</b> {first_date} - {last_date}', info_style))
                except Exception as date_error:
                    logger.warning(f"Date formatting error: {date_error}")
            
            # Generated date
            generated_label = "تاريخ الإنشاء:" if is_arabic else "Generated:"
            story.append(Paragraph(f'<b>{generated_label}</b> {datetime.now().strftime("%Y/%m/%d %H:%M")}', info_style))
            
            story.append(Spacer(1, 20))
            
            # Transaction table header
            transactions_label = "سجل المعاملات" if is_arabic else "Transaction History"
            story.append(Paragraph(transactions_label, header_style))
            
            # Simple table data
            if is_arabic:
                headers = ["الرصيد", "المبلغ", "الوصف", "التاريخ"]
            else:
                headers = ["Date", "Description", "Amount", "Balance"]
                
            data = [headers]
            
            # Calculate running balance
            running_balance = 0.0
            total_lent = 0.0
            total_borrowed = 0.0
            
            # Process transactions chronologically
            for amount, currency, transaction_type, note, created_at in reversed(history):
                try:
                    date_str = datetime.fromisoformat(created_at).strftime("%m/%d")
                    
                    # Calculate balance and description
                    if transaction_type == 'lent':
                        running_balance += amount
                        total_lent += amount
                        if is_arabic:
                            desc = f"أقرضت {amount:,.0f}"
                        else:
                            desc = f"Lent {amount:,.0f}"
                        amount_display = f"+{amount:,.0f}"
                    else:  # borrowed
                        running_balance -= amount  
                        total_borrowed += amount
                        if is_arabic:
                            desc = f"استدنت {amount:,.0f}"
                        else:
                            desc = f"Borrowed {amount:,.0f}"
                        amount_display = f"-{amount:,.0f}"
                    
                    # Add note if available
                    if note:
                        desc += f" ({note})"
                    
                    # Format balance
                    if running_balance > 0:
                        balance_str = f"+{running_balance:,.0f}"
                    elif running_balance < 0:
                        balance_str = f"{running_balance:,.0f}"
                    else:
                        balance_str = "0"
                    
                    if is_arabic:
                        row = [balance_str, amount_display, desc, date_str]
                    else:
                        row = [date_str, desc, amount_display, balance_str]
                        
                    data.append(row)
                    
                except Exception as row_error:
                    logger.warning(f"Error processing transaction row: {row_error}")
                    continue
            
            # Create simplified table
            table = Table(data, colWidths=[2*cm, 6*cm, 3*cm, 2.5*cm])
            table.setStyle(TableStyle([
                # Header styling
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#5AD25B')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#011C1C')),
                ('FONTNAME', (0, 0), (-1, 0), bold_font),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                
                # Data styling
                ('FONTNAME', (0, 1), (-1, -1), base_font),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
                
                # Alignment
                ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Date column
                ('ALIGN', (1, 1), (1, -1), table_alignment), # Description 
                ('ALIGN', (2, 1), (2, -1), 'RIGHT'),   # Amount
                ('ALIGN', (3, 1), (3, -1), 'CENTER'),  # Balance
            ]))
            
            story.append(table)
            story.append(Spacer(1, 25))
            
            # Summary section
            summary_label = "الملخص" if is_arabic else "Summary"
            story.append(Paragraph(summary_label, header_style))
            
            # Summary box with background
            summary_data = []
            
            if is_arabic:
                summary_data.append([f"إجمالي المُقرض: {total_lent:,.0f} دج"])
                summary_data.append([f"إجمالي المُستدان: {total_borrowed:,.0f} دج"])
            else:
                summary_data.append([f"Total Lent: {total_lent:,.0f} DZD"])
                summary_data.append([f"Total Borrowed: {total_borrowed:,.0f} DZD"])
            
            # Final balance with color coding - use plain text without HTML
            final_balance = running_balance
            if final_balance > 0:
                if is_arabic:
                    balance_text = f"الرصيد النهائي: +{final_balance:,.0f} دج (مدين لك)"
                else:
                    balance_text = f"Final Balance: +{final_balance:,.0f} DZD (Owes you)"
                balance_color = colors.green
            elif final_balance < 0:
                if is_arabic:
                    balance_text = f"الرصيد النهائي: {final_balance:,.0f} دج (مدين عليك)"  
                else:
                    balance_text = f"Final Balance: {final_balance:,.0f} DZD (You owe)"
                balance_color = colors.red
            else:
                if is_arabic:
                    balance_text = f"الرصيد النهائي: 0 دج (متصالح)"
                else:
                    balance_text = f"Final Balance: 0 DZD (Settled)"
                balance_color = colors.blue
                
            # Add balance text without HTML formatting
            summary_data.append([balance_text])
            
            # Summary table
            summary_table = Table(summary_data, colWidths=[12*cm])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
                ('FONTNAME', (0, 0), (-1, -1), base_font),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('ALIGN', (0, 0), (-1, -1), table_alignment),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#5AD25B')),
                ('LEFTPADDING', (0, 0), (-1, -1), 15),
                ('RIGHTPADDING', (0, 0), (-1, -1), 15),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                # Color the balance row based on final balance
                ('TEXTCOLOR', (0, -1), (-1, -1), balance_color),
                ('FONTNAME', (0, -1), (-1, -1), bold_font),  # Make balance text bold
            ]))
            
            story.append(summary_table)
            story.append(Spacer(1, 30))
            
            # Footer
            footer_text = f"تم الإنشاء بواسطة Markily • {datetime.now().strftime('%Y/%m/%d')}" if is_arabic else f"Generated by Markily • {datetime.now().strftime('%Y/%m/%d')}"
            footer_style = ParagraphStyle(
                'FooterStyle', fontSize=8, fontName='Helvetica',
                alignment=TA_CENTER, textColor=colors.HexColor('#999999')
            )
            story.append(Paragraph(footer_text, footer_style))
            
            # Build PDF
            doc.build(story)
            buffer.seek(0)
            pdf_bytes = buffer.getvalue()
            
            logger.info(f"PDF generated successfully for user {user_id}, contact {contact_id} - {len(pdf_bytes):,} bytes")
            return pdf_bytes
            
        except Exception as e:
            logger.error(f"Error generating PDF for user {user_id}, contact {contact_id}: {e}")
            import traceback
            logger.error(f"PDF generation traceback: {traceback.format_exc()}")
            return None
    
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
    
    def create_reminder(self, user_id: int, chat_id: int, contact_id: int, 
                       reminder_datetime: datetime, note: str) -> bool:
        """Create a new reminder"""
        try:
            db_path = self.get_db_path(chat_id)
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO reminders (user_id, contact_id, reminder_datetime, note)
                VALUES (?, ?, ?, ?)
            ''', (user_id, contact_id, reminder_datetime, note))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error creating reminder: {e}")
            return False
    
    def get_user_reminders(self, user_id: int, chat_id: int) -> List[Tuple]:
        """Get all active reminders for a user"""
        try:
            db_path = self.get_db_path(chat_id)
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT r.id, c.name, r.reminder_datetime, r.note
                FROM reminders r
                JOIN contacts c ON r.contact_id = c.id
                WHERE r.user_id = ? AND r.is_active = 1
                AND r.reminder_datetime > ?
                ORDER BY r.reminder_datetime ASC
            ''', (user_id, datetime.now()))
            
            reminders = []
            for row in cursor.fetchall():
                reminder_id, contact_name, datetime_str, note = row
                reminder_dt = datetime.fromisoformat(datetime_str)
                reminders.append((reminder_id, contact_name, reminder_dt, note))
            
            conn.close()
            return reminders
        except Exception as e:
            logger.error(f"Error getting reminders: {e}")
            return []
    
    def delete_reminder(self, user_id: int, chat_id: int, reminder_id: int) -> bool:
        """Delete a reminder"""
        try:
            db_path = self.get_db_path(chat_id)
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE reminders 
                SET is_active = 0 
                WHERE id = ? AND user_id = ?
            ''', (reminder_id, user_id))
            
            conn.commit()
            conn.close()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting reminder: {e}")
            return False
    
    def get_balance_with_contact(self, user_id: int, chat_id: int, contact_id: int) -> float:
        """Get balance with a specific contact"""
        try:
            db_path = self.get_db_path(chat_id)
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT SUM(
                    CASE 
                        WHEN transaction_type = 'lent' THEN amount
                        WHEN transaction_type = 'borrowed' THEN -amount
                        WHEN transaction_type = 'paid' THEN -amount
                        ELSE 0
                    END
                ) as balance
                FROM transactions 
                WHERE user_id = ? AND contact_id = ?
            ''', (user_id, contact_id))
            
            result = cursor.fetchone()
            conn.close()
            return result[0] if result[0] is not None else 0.0
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            return 0.0
    
    def get_contact_by_id(self, user_id: int, chat_id: int, contact_id: int) -> Optional[Tuple]:
        """Get contact by ID"""
        try:
            db_path = self.get_db_path(chat_id)
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, name FROM contacts 
                WHERE id = ? AND user_id = ?
            ''', (contact_id, user_id))
            
            result = cursor.fetchone()
            conn.close()
            return result
        except Exception as e:
            logger.error(f"Error getting contact: {e}")
            return None
    
    def schedule_reminder(self, user_id: int, contact_id: int, reminder_dt: datetime, 
                         note: str, contact_name: str, chat_id: int = None):
        """Schedule a reminder job"""
        if chat_id is None:
            chat_id = user_id
        
        job_data = {
            'user_id': user_id,
            'contact_id': contact_id,
            'contact_name': contact_name,
            'note': note,
            'reminder_dt': reminder_dt,
            'chat_id': chat_id
        }
        
        # We'll implement job scheduling in the main function
        # Store this data for now
        if not hasattr(self, 'pending_reminders'):
            self.pending_reminders = []
        self.pending_reminders.append((reminder_dt, job_data))

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
            InlineKeyboardButton(t(user.id, 'set_reminder'), callback_data="action_set_reminder"),
            InlineKeyboardButton(t(user.id, 'view_reminders'), callback_data="action_view_reminders")
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
    
    keyboard = [
        [InlineKeyboardButton(t(user_id, 'export_pdf'), callback_data=f"export_pdf_{contact_id}")],
        [InlineKeyboardButton(t(user_id, 'back_to_menu'), callback_data="back_to_menu")]
    ]
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

async def export_pdf_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Export PDF report for transaction history"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    chat_id = query.message.chat.id
    
    # Extract contact_id from callback data
    contact_id = int(query.data.split('_')[2])
    
    # Get contact info
    contacts = bot.get_user_contacts(user_id, chat_id)
    contact = next((c for c in contacts if c[0] == contact_id), None)
    if not contact:
        await query.edit_message_text(t(user_id, 'contact_not_found'))
        return
    
    contact_name = contact[1]
    
    # Check if there are transactions
    history = bot.get_transaction_history(user_id, contact_id, chat_id)
    if not history:
        await query.edit_message_text(t(user_id, 'no_transactions_pdf', contact_name))
        return
    
    # Show generating message
    await query.edit_message_text(t(user_id, 'generating_pdf'))
    
    # Generate PDF with better error handling
    user_name = query.from_user.first_name or "User"
    
    try:
        pdf_bytes = bot.generate_pdf_report(user_id, contact_id, chat_id, user_name)
        
        if pdf_bytes:
            # Create filename
            safe_contact_name = "".join(c for c in contact_name if c.isalnum() or c in (' ', '-', '_')).strip()
            filename = f"transaction_history_{safe_contact_name}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
            
            # Send PDF file
            pdf_file = io.BytesIO(pdf_bytes)
            pdf_file.name = filename
            
            success_message = t(user_id, 'pdf_generated', contact_name, datetime.now().strftime('%Y-%m-%d %H:%M'))
            
            await query.message.reply_document(
                document=pdf_file,
                filename=filename,
                caption=success_message,
                parse_mode='Markdown'
            )
            
            # Show main menu again after PDF generation
            keyboard = [
                [
                    InlineKeyboardButton(t(user_id, 'lent_money'), callback_data="action_lend"),
                    InlineKeyboardButton(t(user_id, 'borrowed_money'), callback_data="action_borrow")
                ],
                [
                    InlineKeyboardButton(t(user_id, 'add_contact'), callback_data="action_add_contact"),
                    InlineKeyboardButton(t(user_id, 'view_balances'), callback_data="action_balances")
                ],
                [
                    InlineKeyboardButton(t(user_id, 'transaction_history'), callback_data="action_history"),
                    InlineKeyboardButton(t(user_id, 'clear_balance'), callback_data="action_clear")
                ],
                [
                    InlineKeyboardButton(t(user_id, 'set_reminder'), callback_data="action_set_reminder"),
                    InlineKeyboardButton(t(user_id, 'view_reminders'), callback_data="action_view_reminders")
                ],
                [
                    InlineKeyboardButton(t(user_id, 'delete_contact'), callback_data="action_delete_contact"),
                    InlineKeyboardButton(t(user_id, 'language'), callback_data="action_language")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Get user's first name for welcome message
            user_name = query.from_user.first_name or "User"
            welcome_text = t(user_id, 'welcome', user_name)
            
            await query.edit_message_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
            
        else:
            # PDF generation returned None - likely no transaction history
            logger.error(f"PDF generation returned None for user {user_id}, contact {contact_id}")
            
            # Show main menu with error message
            keyboard = [
                [
                    InlineKeyboardButton(t(user_id, 'lent_money'), callback_data="action_lend"),
                    InlineKeyboardButton(t(user_id, 'borrowed_money'), callback_data="action_borrow")
                ],
                [
                    InlineKeyboardButton(t(user_id, 'add_contact'), callback_data="action_add_contact"),
                    InlineKeyboardButton(t(user_id, 'view_balances'), callback_data="action_balances")
                ],
                [
                    InlineKeyboardButton(t(user_id, 'transaction_history'), callback_data="action_history"),
                    InlineKeyboardButton(t(user_id, 'clear_balance'), callback_data="action_clear")
                ],
                [
                    InlineKeyboardButton(t(user_id, 'set_reminder'), callback_data="action_set_reminder"),
                    InlineKeyboardButton(t(user_id, 'view_reminders'), callback_data="action_view_reminders")
                ],
                [
                    InlineKeyboardButton(t(user_id, 'delete_contact'), callback_data="action_delete_contact"),
                    InlineKeyboardButton(t(user_id, 'language'), callback_data="action_language")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Get user's first name for welcome message
            user_name = query.from_user.first_name or "User"
            welcome_text = t(user_id, 'welcome', user_name)
            
            # Show error message indicating no transaction history with helpful guidance
            if get_user_language(user_id) == 'en':
                no_history_msg = f"📋 **No Transaction History**\n\nYou don't have any transactions with **{contact_name}** yet.\n\n💡 **Get Started:**\n• Tap **Lent Money** if they owe you\n• Tap **Borrowed Money** if you owe them"
            else:
                no_history_msg = f"📋 **لا يوجد تاريخ معاملات**\n\nليس لديك أي معاملات مع **{contact_name}** حتى الآن.\n\n💡 **ابدأ الآن:**\n• اضغط **أقرضت مالاً** إذا كان مديناً لك\n• اضغط **استدنت مالاً** إذا كنت مديناً له"
            
            # Create quick action keyboard with highlighted lend/borrow buttons
            keyboard = [
                [
                    InlineKeyboardButton(f"💸 {t(user_id, 'lent_money')}", callback_data="action_lend"),
                    InlineKeyboardButton(f"💰 {t(user_id, 'borrowed_money')}", callback_data="action_borrow")
                ],
                [
                    InlineKeyboardButton(t(user_id, 'add_contact'), callback_data="action_add_contact"),
                    InlineKeyboardButton(t(user_id, 'view_balances'), callback_data="action_balances")
                ],
                [
                    InlineKeyboardButton(t(user_id, 'transaction_history'), callback_data="action_history"),
                    InlineKeyboardButton(t(user_id, 'clear_balance'), callback_data="action_clear")
                ],
                [
                    InlineKeyboardButton(t(user_id, 'set_reminder'), callback_data="action_set_reminder"),
                    InlineKeyboardButton(t(user_id, 'view_reminders'), callback_data="action_view_reminders")
                ],
                [
                    InlineKeyboardButton(t(user_id, 'delete_contact'), callback_data="action_delete_contact"),
                    InlineKeyboardButton(t(user_id, 'language'), callback_data="action_language")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Show the helpful message with quick actions
            await query.edit_message_text(no_history_msg, reply_markup=reply_markup, parse_mode='Markdown')
            
    except Exception as e:
        logger.error(f"Exception during PDF generation for user {user_id}, contact {contact_id}: {str(e)}")
        logger.error(f"Traceback: ", exc_info=True)
        
        # Show main menu with error message
        keyboard = [
            [
                InlineKeyboardButton(t(user_id, 'lent_money'), callback_data="action_lend"),
                InlineKeyboardButton(t(user_id, 'borrowed_money'), callback_data="action_borrow")
            ],
            [
                InlineKeyboardButton(t(user_id, 'add_contact'), callback_data="action_add_contact"),
                InlineKeyboardButton(t(user_id, 'view_balances'), callback_data="action_balances")
            ],
            [
                InlineKeyboardButton(t(user_id, 'transaction_history'), callback_data="action_history"),
                InlineKeyboardButton(t(user_id, 'clear_balance'), callback_data="action_clear")
            ],
            [
                InlineKeyboardButton(t(user_id, 'set_reminder'), callback_data="action_set_reminder"),
                InlineKeyboardButton(t(user_id, 'view_reminders'), callback_data="action_view_reminders")
            ],
            [
                InlineKeyboardButton(t(user_id, 'delete_contact'), callback_data="action_delete_contact"),
                InlineKeyboardButton(t(user_id, 'language'), callback_data="action_language")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Get user's first name for welcome message
        user_name = query.from_user.first_name or "User"
        welcome_text = t(user_id, 'welcome', user_name)
        
        # Show error message with exception details
        error_text = t(user_id, 'pdf_error') + f" (Error: {str(e)})" + "\n\n" + welcome_text
        await query.edit_message_text(error_text, reply_markup=reply_markup, parse_mode='Markdown')

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

def parse_reminder_datetime(datetime_text: str) -> Optional[datetime]:
    """Parse various date/time formats for reminders"""
    datetime_text = datetime_text.lower().strip()
    now = datetime.now()
    
    # Handle relative dates
    if 'tomorrow' in datetime_text:
        base_date = now + timedelta(days=1)
        # Extract time if provided
        time_match = re.search(r'(\d{1,2})\s*(am|pm|a\.m\.|p\.m\.)', datetime_text)
        if time_match:
            hour = int(time_match.group(1))
            period = time_match.group(2)
            if 'p' in period and hour != 12:
                hour += 12
            elif 'a' in period and hour == 12:
                hour = 0
            return base_date.replace(hour=hour, minute=0, second=0, microsecond=0)
        return base_date.replace(hour=9, minute=0, second=0, microsecond=0)
    
    elif 'next monday' in datetime_text or 'monday' in datetime_text:
        days_ahead = 7 - now.weekday()  # Monday is 0
        if days_ahead <= 0:
            days_ahead += 7
        base_date = now + timedelta(days=days_ahead)
        # Extract time if provided
        time_match = re.search(r'(\d{1,2})\s*(am|pm|a\.m\.|p\.m\.)', datetime_text)
        if time_match:
            hour = int(time_match.group(1))
            period = time_match.group(2)
            if 'p' in period and hour != 12:
                hour += 12
            elif 'a' in period and hour == 12:
                hour = 0
            return base_date.replace(hour=hour, minute=0, second=0, microsecond=0)
        return base_date.replace(hour=9, minute=0, second=0, microsecond=0)
    
    # Try various date formats
    formats = [
        '%Y-%m-%d %H:%M',
        '%Y-%m-%d %H:%M:%S',
        '%d-%m-%Y %H:%M',
        '%d/%m/%Y %H:%M',
        '%m/%d/%Y %H:%M',
        '%Y-%m-%d',
        '%d-%m-%Y',
        '%d/%m/%Y',
        '%m/%d/%Y'
    ]
    
    # Handle formats like "Aug 27 10AM", "August 27 10AM"
    month_pattern = r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})\s*(\d{1,2})\s*(am|pm|a\.m\.|p\.m\.)?'
    month_match = re.search(month_pattern, datetime_text)
    if month_match:
        month_str = month_match.group(1)
        day = int(month_match.group(2))
        hour = int(month_match.group(3))
        period = month_match.group(4)
        
        # Convert month name to number
        month_map = {
            'jan': 1, 'january': 1, 'feb': 2, 'february': 2, 'mar': 3, 'march': 3,
            'apr': 4, 'april': 4, 'may': 5, 'jun': 6, 'june': 6,
            'jul': 7, 'july': 7, 'aug': 8, 'august': 8, 'sep': 9, 'september': 9,
            'oct': 10, 'october': 10, 'nov': 11, 'november': 11, 'dec': 12, 'december': 12
        }
        month = month_map.get(month_str[:3], 8)  # Default to August
        
        if period and 'p' in period and hour != 12:
            hour += 12
        elif period and 'a' in period and hour == 12:
            hour = 0
            
        year = now.year
        if month < now.month or (month == now.month and day < now.day):
            year += 1
            
        try:
            return datetime(year, month, day, hour, 0, 0)
        except ValueError:
            pass
    
    # Try using dateutil parser as fallback
    try:
        return date_parser.parse(datetime_text, fuzzy=True)
    except:
        pass
    
    # Try standard formats
    for fmt in formats:
        try:
            return datetime.strptime(datetime_text, fmt)
        except ValueError:
            continue
    
    return None

async def start_set_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the process of setting a reminder"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    chat_id = query.message.chat.id
    
    # Get user's contacts
    contacts = bot.get_user_contacts(user_id, chat_id)
    
    if not contacts:
        keyboard = [
            [InlineKeyboardButton(t(user_id, 'add_contact_first'), callback_data="action_add_contact")],
            [InlineKeyboardButton(t(user_id, 'back_to_menu'), callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(t(user_id, 'no_contacts'), reply_markup=reply_markup)
        return ConversationHandler.END
    
    # Create contact selection keyboard
    keyboard = []
    for contact in contacts:
        keyboard.append([InlineKeyboardButton(contact[1], callback_data=f"reminder_contact_{contact[0]}")])
    
    keyboard.append([InlineKeyboardButton(t(user_id, 'cancel'), callback_data="back_to_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(t(user_id, 'reminder_for_whom'), reply_markup=reply_markup)
    return WAITING_FOR_REMINDER_CONTACT

async def handle_reminder_contact_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle contact selection for reminder"""
    query = update.callback_query
    await query.answer()
    
    if not query.data.startswith("reminder_contact_"):
        return ConversationHandler.END
    
    contact_id = query.data.split("_")[-1]
    user_id = query.from_user.id
    
    # Store contact_id in context
    context.user_data['reminder_contact_id'] = contact_id
    
    # Show date selection options
    keyboard = [
        [
            InlineKeyboardButton(t(user_id, 'today'), callback_data="date_today"),
            InlineKeyboardButton(t(user_id, 'tomorrow'), callback_data="date_tomorrow")
        ],
        [
            InlineKeyboardButton(t(user_id, 'this_weekend'), callback_data="date_this_weekend"),
            InlineKeyboardButton(t(user_id, 'next_monday'), callback_data="date_next_monday")
        ],
        [
            InlineKeyboardButton(t(user_id, 'next_week'), callback_data="date_next_week"),
            InlineKeyboardButton(t(user_id, 'custom_date'), callback_data="date_custom")
        ],
        [InlineKeyboardButton(t(user_id, 'cancel'), callback_data="back_to_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(t(user_id, 'reminder_date_time'), reply_markup=reply_markup)
    return WAITING_FOR_REMINDER_DATETIME

async def handle_reminder_datetime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle date selection or custom datetime input for reminder"""
    if update.callback_query:
        # Handle button selection for date
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        date_choice = query.data
        
        # Calculate the date based on selection
        now = datetime.now()
        if date_choice == "date_today":
            selected_date = now
            date_text = "Today"
        elif date_choice == "date_tomorrow":
            selected_date = now + timedelta(days=1)
            date_text = "Tomorrow"
        elif date_choice == "date_this_weekend":
            # Find next Saturday
            days_until_saturday = (5 - now.weekday()) % 7
            if days_until_saturday == 0:  # If today is Saturday
                days_until_saturday = 1   # Go to Sunday
            selected_date = now + timedelta(days=days_until_saturday)
            date_text = "This weekend"
        elif date_choice == "date_next_monday":
            # Find next Monday
            days_until_monday = (7 - now.weekday()) % 7
            if days_until_monday == 0:  # If today is Monday
                days_until_monday = 7    # Next Monday
            selected_date = now + timedelta(days=days_until_monday)
            date_text = "Next Monday"
        elif date_choice == "date_next_week":
            selected_date = now + timedelta(days=7)
            date_text = "Next week"
        elif date_choice == "date_custom":
            # Ask for custom date input
            await query.edit_message_text(
                "📅 Send custom date and time:\n\n💡 Examples:\n• Aug 27 10AM\n• 2025-08-27 14:30\n• Next Monday 9AM"
            )
            return WAITING_FOR_REMINDER_DATETIME
        else:
            return ConversationHandler.END
        
        # Store the selected date and show time options
        context.user_data['reminder_date'] = selected_date.date()
        context.user_data['date_text'] = date_text
        
        # Show time selection
        keyboard = [
            [
                InlineKeyboardButton(t(user_id, 'morning_9am'), callback_data="time_09:00"),
                InlineKeyboardButton(t(user_id, 'morning_10am'), callback_data="time_10:00")
            ],
            [
                InlineKeyboardButton(t(user_id, 'afternoon_2pm'), callback_data="time_14:00"),
                InlineKeyboardButton(t(user_id, 'afternoon_5pm'), callback_data="time_17:00")
            ],
            [
                InlineKeyboardButton(t(user_id, 'evening_8pm'), callback_data="time_20:00"),
                InlineKeyboardButton(t(user_id, 'custom_time'), callback_data="time_custom")
            ],
            [InlineKeyboardButton(t(user_id, 'cancel'), callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(t(user_id, 'select_time', date_text), reply_markup=reply_markup)
        return WAITING_FOR_REMINDER_TIME
    
    else:
        # Handle custom text input for datetime
        user_id = update.effective_user.id
        datetime_text = update.message.text
        
        # Parse the datetime
        reminder_dt = parse_reminder_datetime(datetime_text)
        
        if not reminder_dt:
            await update.message.reply_text(t(user_id, 'invalid_datetime'))
            return WAITING_FOR_REMINDER_DATETIME
        
        # Check if datetime is in the future
        if reminder_dt <= datetime.now():
            await update.message.reply_text(t(user_id, 'invalid_datetime'))
            return WAITING_FOR_REMINDER_DATETIME
        
        # Store datetime in context
        context.user_data['reminder_datetime'] = reminder_dt
        
        await update.message.reply_text(t(user_id, 'reminder_note'))
        return WAITING_FOR_REMINDER_NOTE

async def handle_reminder_time_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle time selection for reminder"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    time_choice = query.data
    
    if time_choice == "time_custom":
        # Ask for custom time input
        await query.edit_message_text(
            "⏰ Send custom time:\n\n💡 Examples:\n• 10AM\n• 2:30 PM\n• 14:30"
        )
        return WAITING_FOR_REMINDER_TIME
    
    # Parse the selected time
    if time_choice.startswith("time_"):
        time_str = time_choice.replace("time_", "")
        hour, minute = map(int, time_str.split(":"))
        
        # Get the stored date
        selected_date = context.user_data.get('reminder_date')
        if not selected_date:
            await query.edit_message_text("❌ Error: Date not found. Please start again.")
            return ConversationHandler.END
        
        # Combine date and time
        reminder_dt = datetime.combine(selected_date, datetime.min.time().replace(hour=hour, minute=minute))
        
        # Check if datetime is in the future
        if reminder_dt <= datetime.now():
            await query.edit_message_text("❌ Please select a future time.")
            return WAITING_FOR_REMINDER_TIME
        
        # Store datetime in context
        context.user_data['reminder_datetime'] = reminder_dt
        
        await query.edit_message_text(t(user_id, 'reminder_note'))
        return WAITING_FOR_REMINDER_NOTE
    
    return ConversationHandler.END

async def handle_custom_time_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle custom time text input"""
    user_id = update.effective_user.id
    time_text = update.message.text.strip()
    
    # Parse time from various formats
    try:
        # Try to parse time formats like "10AM", "2:30 PM", "14:30"
        time_text_lower = time_text.lower()
        
        if 'am' in time_text_lower or 'pm' in time_text_lower:
            # Handle 12-hour format
            time_part = time_text_lower.replace('am', '').replace('pm', '').replace('a.m.', '').replace('p.m.', '').strip()
            
            if ':' in time_part:
                hour_str, minute_str = time_part.split(':')
                hour = int(hour_str)
                minute = int(minute_str)
            else:
                hour = int(time_part)
                minute = 0
            
            # Convert to 24-hour format
            if 'pm' in time_text_lower or 'p.m.' in time_text_lower:
                if hour != 12:
                    hour += 12
            elif ('am' in time_text_lower or 'a.m.' in time_text_lower) and hour == 12:
                hour = 0
                
        else:
            # Handle 24-hour format
            if ':' in time_text:
                hour_str, minute_str = time_text.split(':')
                hour = int(hour_str)
                minute = int(minute_str)
            else:
                hour = int(time_text)
                minute = 0
        
        # Validate time
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError("Invalid time")
            
        # Get the stored date
        selected_date = context.user_data.get('reminder_date')
        if not selected_date:
            await update.message.reply_text("❌ Error: Date not found. Please start again.")
            return ConversationHandler.END
        
        # Combine date and time
        reminder_dt = datetime.combine(selected_date, datetime.min.time().replace(hour=hour, minute=minute))
        
        # Check if datetime is in the future
        if reminder_dt <= datetime.now():
            await update.message.reply_text("❌ Please select a future time.")
            return WAITING_FOR_REMINDER_TIME
        
        # Store datetime in context
        context.user_data['reminder_datetime'] = reminder_dt
        
        await update.message.reply_text(t(user_id, 'reminder_note'))
        return WAITING_FOR_REMINDER_NOTE
        
    except (ValueError, IndexError):
        await update.message.reply_text("❌ Invalid time format. Try: 10AM, 2:30 PM, or 14:30")
        return WAITING_FOR_REMINDER_TIME

async def handle_reminder_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle note input for reminder"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    note = update.message.text
    
    # Get data from context
    contact_id = context.user_data.get('reminder_contact_id')
    reminder_dt = context.user_data.get('reminder_datetime')
    
    if not contact_id or not reminder_dt:
        await update.message.reply_text("❌ Error setting reminder. Please try again.")
        return ConversationHandler.END
    
    # Get contact name
    contact = bot.get_contact_by_id(user_id, chat_id, contact_id)
    if not contact:
        await update.message.reply_text(t(user_id, 'contact_not_found'))
        return ConversationHandler.END
    
    contact_name = contact[1]
    
    # Save reminder to database
    if bot.create_reminder(user_id, chat_id, contact_id, reminder_dt, note):
        # Format datetime for display
        formatted_dt = reminder_dt.strftime('%Y-%m-%d %H:%M')
        
        success_message = t(user_id, 'reminder_set', formatted_dt, contact_name, note)
        
        keyboard = [[InlineKeyboardButton(t(user_id, 'back_to_menu'), callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(success_message, reply_markup=reply_markup, parse_mode='Markdown')
        
        # Schedule the reminder
        bot.schedule_reminder(user_id, contact_id, reminder_dt, note, contact_name, chat_id)
    else:
        await update.message.reply_text("❌ Error saving reminder. Please try again.")
    
    # Clear context
    context.user_data.clear()
    return ConversationHandler.END

async def view_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View all active reminders for the user"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    chat_id = query.message.chat.id
    
    reminders = bot.get_user_reminders(user_id, chat_id)
    
    if not reminders:
        keyboard = [[InlineKeyboardButton(t(user_id, 'back_to_menu'), callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(t(user_id, 'no_reminders'), reply_markup=reply_markup)
        return
    
    message = t(user_id, 'your_reminders') + "\n\n"
    keyboard = []
    
    for reminder in reminders:
        reminder_id, contact_name, reminder_dt, note = reminder
        formatted_dt = reminder_dt.strftime('%Y-%m-%d %H:%M')
        
        reminder_text = f"⏰ **{formatted_dt}**\n👤 {contact_name}\n📝 {note}\n"
        message += reminder_text + "\n"
        
        keyboard.append([
            InlineKeyboardButton(f"🗑️ {contact_name[:20]}...", callback_data=f"delete_reminder_{reminder_id}")
        ])
    
    keyboard.append([InlineKeyboardButton(t(user_id, 'back_to_menu'), callback_data="back_to_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def delete_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete a reminder"""
    query = update.callback_query
    await query.answer()
    
    reminder_id = query.data.split("_")[-1]
    user_id = query.from_user.id
    chat_id = query.message.chat.id
    
    if bot.delete_reminder(user_id, chat_id, reminder_id):
        await query.answer(t(user_id, 'reminder_deleted'))
        # Refresh the reminders view
        await view_reminders(update, context)
    else:
        await query.answer("❌ Error deleting reminder")

async def send_reminder_notification(context: ContextTypes.DEFAULT_TYPE):
    """Send reminder notification to user"""
    job_data = context.job.data
    user_id = job_data['user_id']
    contact_name = job_data['contact_name']
    note = job_data['note']
    reminder_dt = job_data['reminder_dt']
    
    # Get current balance with contact
    chat_id = job_data.get('chat_id', user_id)  # Use user_id as fallback for private chats
    contact_id = job_data['contact_id']
    
    # Get balance info
    balance = bot.get_balance_with_contact(user_id, chat_id, contact_id)
    balance_text = "0 DZD"
    if balance != 0:
        if balance > 0:
            balance_text = f"{balance:,.0f} DZD (owes you)"
        else:
            balance_text = f"{abs(balance):,.0f} DZD (you owe)"
    
    reminder_message = t(user_id, 'reminder_due', contact_name, note, reminder_dt.strftime('%Y-%m-%d %H:%M'), balance_text)
    
    try:
        await context.bot.send_message(chat_id=user_id, text=reminder_message, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Failed to send reminder to user {user_id}: {e}")

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
    
    elif data.startswith("export_pdf_"):
        await export_pdf_report(update, context)
        return ConversationHandler.END
    
    elif data == "action_set_reminder":
        return await start_set_reminder(update, context)
    
    elif data == "action_view_reminders":
        await view_reminders(update, context)
        return ConversationHandler.END
    
    elif data.startswith("reminder_contact_"):
        return await handle_reminder_contact_selection(update, context)
    
    elif data.startswith("date_"):
        return await handle_reminder_datetime(update, context)
    
    elif data.startswith("time_"):
        return await handle_reminder_time_selection(update, context)
    
    elif data.startswith("delete_reminder_"):
        await delete_reminder(update, context)
        return ConversationHandler.END
    
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

async def reminder_checker(bot_instance):
    """Periodically check for due reminders and send notifications"""
    while True:
        try:
            now = datetime.now()
            # Check all chat databases for due reminders
            db_files = [f for f in os.listdir(bot.db_base_path or ".") if f.startswith("markily_chat_") and f.endswith(".db")]
            
            for db_file in db_files:
                chat_id = int(db_file.split("_")[2].split(".")[0])
                db_path = os.path.join(bot.db_base_path or ".", db_file)
                
                try:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        SELECT r.id, r.user_id, c.name, r.note, r.reminder_datetime, r.contact_id
                        FROM reminders r
                        JOIN contacts c ON r.contact_id = c.id
                        WHERE r.is_active = 1 
                        AND r.reminder_datetime <= ?
                        AND r.reminder_datetime > ?
                    ''', (now, now - timedelta(minutes=5)))  # 5 minute window to avoid missing reminders
                    
                    due_reminders = cursor.fetchall()
                    
                    for reminder in due_reminders:
                        reminder_id, user_id, contact_name, note, reminder_datetime_str, contact_id = reminder
                        reminder_dt = datetime.fromisoformat(reminder_datetime_str)
                        
                        # Get balance with contact
                        balance = bot.get_balance_with_contact(user_id, chat_id, contact_id)
                        balance_text = "0 DZD"
                        if balance != 0:
                            if balance > 0:
                                balance_text = f"{balance:,.0f} DZD (owes you)"
                            else:
                                balance_text = f"{abs(balance):,.0f} DZD (you owe)"
                        
                        reminder_message = t(user_id, 'reminder_due', contact_name, note, reminder_dt.strftime('%Y-%m-%d %H:%M'), balance_text)
                        
                        try:
                            await bot_instance.send_message(chat_id=user_id, text=reminder_message, parse_mode='Markdown')
                            
                            # Mark reminder as sent (deactivate)
                            cursor.execute('UPDATE reminders SET is_active = 0 WHERE id = ?', (reminder_id,))
                            conn.commit()
                            
                        except Exception as e:
                            logger.error(f"Failed to send reminder to user {user_id}: {e}")
                    
                    conn.close()
                    
                except Exception as e:
                    logger.error(f"Error checking reminders in {db_file}: {e}")
                    
        except Exception as e:
            logger.error(f"Error in reminder_checker: {e}")
        
        # Wait 60 seconds before next check
        await asyncio.sleep(60)

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
            CallbackQueryHandler(button_callback, pattern="^action_set_reminder$"),
        ],
        states={
            WAITING_FOR_CONTACT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_contact_name_input)],
            WAITING_FOR_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_amount_input)],
            WAITING_FOR_NOTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_note_input)],
            WAITING_FOR_REMINDER_CONTACT: [CallbackQueryHandler(handle_reminder_contact_selection, pattern="^reminder_contact_")],
            WAITING_FOR_REMINDER_DATETIME: [
                CallbackQueryHandler(handle_reminder_datetime, pattern="^date_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_reminder_datetime)
            ],
            WAITING_FOR_REMINDER_TIME: [
                CallbackQueryHandler(handle_reminder_time_selection, pattern="^time_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_custom_time_input)
            ],
            WAITING_FOR_REMINDER_NOTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_reminder_note)],
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
    print("⏰ Reminder system enabled")
    
    # Start reminder checker
    asyncio.create_task(reminder_checker(application.bot))
    
    await application.start()
    await application.updater.start_polling()
    
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        print("\n👋 Shutting down Markily Bot...")
    finally:
        await application.updater.stop()
        await application.stop()
        await application.shutdown()

if __name__ == '__main__':
    asyncio.run(main())
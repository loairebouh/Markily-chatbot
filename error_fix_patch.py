"""
Fix for the 403 error in Markily Telegram Bot
This patch adds error handling to the start function and other message-sending functions
to gracefully handle permission errors (403) when messaging users
"""

# 1. Add this patch to your error_handler function:

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle Telegram errors gracefully"""
    logger.warning('Exception while handling an update:', exc_info=context.error)

    # Get the error from the context
    error = context.error

    # Handle forbidden errors gracefully
    if "Forbidden" in str(error) or "403" in str(error):
        logger.warning(f"Permission denied (403) when messaging a user. They may have blocked the bot or the bot was removed from a group.")
        return  # Just log and continue, don't crash

    # Log all errors
    logger.error(f"Update {update} caused error {error}")

# 2. Replace your start function with this version that includes error handling:

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

    try:
        if update.message:
            await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.callback_query.edit_message_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error sending welcome message to {user.id}: {e}")
        # Don't re-raise the exception - the bot should continue running even if
        # it can't message a particular user

# 3. Add this general helper function for safe message sending:

async def safe_send_message(chat_id, text, bot, parse_mode=None, reply_markup=None):
    """Send a message with error handling to prevent crashes on permission errors"""
    try:
        return await bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode=parse_mode,
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Error sending message to {chat_id}: {e}")
        return None

# You can use safe_send_message in your reminder notifications and other places
# where you send messages to users outside of direct command responses

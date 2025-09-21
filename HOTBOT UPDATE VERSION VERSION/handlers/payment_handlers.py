from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging
from database import Database

logger = logging.getLogger(__name__)

# Initialize database
db = Database("bot_database.db")

async def handle_transaction_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle transaction ID input for deposits."""
    transaction_id = update.message.text
    amount = context.user_data.get('deposit_amount', 0)
    user_id = update.effective_user.id
    
    # In a real implementation, you would have different payment methods
    # and details. Here we'll use a generic approach.
    
    # Save deposit request to database
    db.add_deposit_request(user_id, amount, "generic", transaction_id)
    
    # Notify admins
    await notify_admins_about_deposit(context.bot, user_id, amount, transaction_id)
    
    # Clear state
    context.user_data.pop('awaiting_input', None)
    context.user_data.pop('deposit_amount', None)
    
    await update.message.reply_text(
        "Your deposit request has been submitted and is pending admin approval. "
        "You will be notified once it's processed.",
        reply_markup=ReplyKeyboardMarkup([["🏠 Main Menu"]], resize_keyboard=True)
    )

async def notify_admins_about_deposit(bot, user_id, amount, transaction_id):
    """Notify all admins about a new deposit request."""
    from config import ADMIN_IDS
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"approve_deposit_{user_id}_{amount}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_deposit_{user_id}_{amount}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message_text = f"""
    🆕 New Deposit Request
    User: {user_id}
    Amount: ৳{amount:.2f}
    Transaction ID: {transaction_id}
    """
    
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                message_text,
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.error(f"Failed to notify admin {admin_id}: {e}")

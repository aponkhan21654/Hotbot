from telegram import Update
from telegram.ext import ContextTypes
import logging
from database import Database

logger = logging.getLogger(__name__)

# Initialize database
db = Database("bot_database.db")

async def approve_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, amount: float):
    """Approve a deposit request."""
    query = update.callback_query
    await query.answer()
    
    # Update user balance
    db.update_balance(user_id, amount)
    
    # Update deposit status in database
    db.update_deposit_status(user_id, amount, "approved")
    
    # Notify user
    try:
        await context.bot.send_message(
            user_id,
            f"✅ Your deposit of ৳{amount:.2f} has been approved! Your new balance is ৳{db.get_balance(user_id):.2f}"
        )
    except Exception as e:
        logger.error(f"Could not notify user {user_id}: {e}")
    
    await query.edit_message_text(f"Deposit of ৳{amount:.2f} for user {user_id} has been approved.")

async def reject_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, amount: float):
    """Reject a deposit request."""
    query = update.callback_query
    await query.answer()
    
    # Update deposit status in database
    db.update_deposit_status(user_id, amount, "rejected")
    
    # Notify user
    try:
        await context.bot.send_message(
            user_id,
            f"❌ Your deposit request of ৳{amount:.2f} has been rejected. Please contact support if you believe this is an error."
        )
    except Exception as e:
        logger.error(f"Could not notify user {user_id}: {e}")
    
    await query.edit_message_text(f"Deposit of ৳{amount:.2f} for user {user_id} has been rejected.")
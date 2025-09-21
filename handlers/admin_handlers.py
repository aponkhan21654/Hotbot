from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackContext
import logging

# ... আপনার existing code ...

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline keyboard button presses."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith("buy_"):
        # Handle purchase
        parts = data.split("_")
        account_type = parts[1]
        quantity = int(parts[2])
        await process_purchase(update, context, account_type, quantity)
    elif data.startswith("custom_"):
        account_type = data.split("_")[1]
        context.user_data['awaiting_input'] = f"custom_{account_type}"
        await query.edit_message_text(f"Please enter the quantity of {account_type} accounts you want to purchase:")
    elif data.startswith("bulk_"):
        account_type = data.split("_")[1]
        await show_bulk_options(update, context, account_type)
    elif data == "cancel":
        await query.edit_message_text("Order cancelled.")
    elif data.startswith("approve_deposit_"):
        # Handle deposit approval
        parts = data.split("_")
        user_id = int(parts[2])
        amount = float(parts[3])
        await payment_handlers.approve_deposit(update, context, user_id, amount)
    elif data.startswith("reject_deposit_"):
        # Handle deposit rejection
        parts = data.split("_")
        user_id = int(parts[2])
        amount = float(parts[3])
        await payment_handlers.reject_deposit(update, context, user_id, amount)
    else:
        await query.edit_message_text(f"Unknown command: {data}")
    
    # Add more callback handlers for other features
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackContext
import logging
from datetime import datetime
import openpyxl
import aiohttp
import asyncio
from config import HOTMAIL_API, GMAIL_API
from database import Database

logger = logging.getLogger(__name__)

# Initialize database
db = Database("bot_database.db")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    referral_code = None
    
    # Check if user was referred
    if context.args:
        referral_code = context.args[0]
        referred_by = db.get_user_id_by_referral_code(referral_code)
    else:
        referred_by = None
    
    # Add user to database
    db.add_user(user.id, user.username, referral_code, referred_by)
    
    # Welcome message
    welcome_text = f"""
    👋 Welcome {user.first_name} to HotBot!

    🔥 We offer premium accounts at competitive prices:
    • Hotmail Accounts
    • Outlook Accounts
    • FB Gmail Accounts

    💎 Also get verification codes for:
    • Hotmail/Outlook
    • Gmail

    Use the menu below to get started!
    """
    
    # Create main menu keyboard
    keyboard = [
        ["🔥 Hotmail Accounts", "🔵 Outlook Accounts"],
        ["📧 FB Gmail Accounts", "💎 Deposit"],
        ["💰 Balance", "🆘 Support"],
        ["🔓 Get Code", "⭐ Special Offers"],
        ["🎁 Bonus & Referral"]
    ]
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages and route to appropriate handlers."""
    message_text = update.message.text
    
    if message_text == "🔥 Hotmail Accounts":
        await show_accounts(update, context, "hotmail")
    elif message_text == "🔵 Outlook Accounts":
        await show_accounts(update, context, "outlook")
    elif message_text == "📧 FB Gmail Accounts":
        await show_accounts(update, context, "fb_gmail")
    elif message_text == "💎 Deposit":
        await start_deposit(update, context)
    elif message_text == "💰 Balance":
        await show_balance(update, context)
    elif message_text == "🆘 Support":
        await show_support(update, context)
    elif message_text == "🔓 Get Code":
        await show_code_options(update, context)
    elif message_text == "⭐ Special Offers":
        await show_special_offers(update, context)
    elif message_text == "🎁 Bonus & Referral":
        await show_referral_info(update, context)
    else:
        # Check if we're in a multi-step process
        if 'awaiting_input' in context.user_data:
            process_type = context.user_data['awaiting_input']
            if process_type == 'deposit_amount':
                await handle_deposit_amount(update, context)
            elif process_type == 'transaction_id':
                await handle_transaction_id(update, context)
            elif process_type == 'hotmail_credentials':
                await handle_hotmail_credentials(update, context)
            elif process_type == 'gmail_email':
                await handle_gmail_email(update, context)
        else:
            await update.message.reply_text("I didn't understand that command. Please use the menu.")

async def show_accounts(update: Update, context: ContextTypes.DEFAULT_TYPE, account_type: str) -> None:
    """Show available accounts with purchase options."""
    # Get stock count and price from database
    stock_count = get_stock_count(account_type)
    price = db.get_price(account_type)
    
    keyboard = [
        [
            InlineKeyboardButton(f"1 Pcs - ৳{price:.2f}", callback_data=f"buy_{account_type}_1"),
            InlineKeyboardButton(f"5 Pcs - ৳{price*5:.2f}", callback_data=f"buy_{account_type}_5")
        ],
        [
            InlineKeyboardButton("Custom Quantity", callback_data=f"custom_{account_type}"),
            InlineKeyboardButton("Bulk Order", callback_data=f"bulk_{account_type}")
        ],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = f"""
    {get_account_emoji(account_type)} {account_type.capitalize()} Accounts
    Stock: {stock_count}
    Price: ৳{price:.2f} per account
    
    Select quantity:
    """
    
    await update.message.reply_text(text, reply_markup=reply_markup)

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
    
    # Add more callback handlers for other features

async def start_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start the deposit process."""
    context.user_data['awaiting_input'] = 'deposit_amount'
    await update.message.reply_text("Please enter the amount you want to deposit (in BDT):")

async def handle_deposit_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle deposit amount input."""
    try:
        amount = float(update.message.text)
        if amount <= 0:
            await update.message.reply_text("Please enter a positive amount.")
            return
        
        context.user_data['deposit_amount'] = amount
        context.user_data['awaiting_input'] = 'transaction_id'
        
        # Show payment methods
        keyboard = [
            ["💙 BKash", "💚 Nagad"],
            ["💜 Rocket", "📞 Bank Transfer"],
            ["💳 Card", "🔙 Cancel"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            f"Please select a payment method for ৳{amount:.2f}:",
            reply_markup=reply_markup
        )
    except ValueError:
        await update.message.reply_text("Please enter a valid number.")

# Additional handler functions would be implemented for:
# - show_balance
# - show_support
# - show_code_options
# - process_code_request
# - show_special_offers
# - show_referral_info
# - And all other user-facing features

async def get_hotmail_code(email, password, token, client_id):
    """Call Hotmail/Outlook API to get verification code."""
    params = {
        'email': email,
        'password': password,
        'token': token,
        'client_id': client_id
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(HOTMAIL_API, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('code', 'No code found')
                else:
                    return f"API error: {response.status}"
    except Exception as e:
        return f"Error: {str(e)}"

async def get_gmail_code(email):
    """Call Gmail API to get verification code."""
    params = {'email': email}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(GMAIL_API, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('code', 'No code found')
                else:
                    return f"API error: {response.status}"
    except Exception as e:
        return f"Error: {str(e)}"

def get_stock_count(account_type):
    """Get stock count from Excel file."""
    try:
        file_path = f"data/{account_type}_data.xlsx"
        wb = openpyxl.load_workbook(file_path)
        sheet = wb.active
        return sheet.max_row - 1  # Subtract header row
    except:
        return 0

def get_account_emoji(account_type):
    """Get emoji for account type."""
    emojis = {
        'hotmail': '🔥',
        'outlook': '🔵',
        'fb_gmail': '📧'
    }
    return emojis.get(account_type, '')
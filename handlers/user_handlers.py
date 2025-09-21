from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackContext
import logging
from datetime import datetime
import openpyxl
import aiohttp
import asyncio
import os
from database import Database

logger = logging.getLogger(__name__)

# Initialize database
db = Database("bot_database.db")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    referral_code = None
    referred_by = None
    
    # Check if user was referred
    if context.args:
        referral_code = context.args[0]
        referred_by = db.get_user_id_by_referral_code(referral_code)
    
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
    
    await show_main_menu(update, context, welcome_text)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, text=None) -> None:
    """Show main menu to user."""
    if text is None:
        text = "🏠 Main Menu - Select an option:"
    
    keyboard = [
        ["🔥 Hotmail Accounts", "🔵 Outlook Accounts"],
        ["📧 FB Gmail Accounts", "💎 Deposit"],
        ["💰 Balance", "🆘 Support"],
        ["🔓 Get Code", "⭐ Special Offers"],
        ["🎁 Bonus & Referral"]
    ]
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    if hasattr(update, 'message'):
        await update.message.reply_text(text, reply_markup=reply_markup)
    elif hasattr(update, 'callback_query'):
        await update.callback_query.message.reply_text(text, reply_markup=reply_markup)

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
    else:
        await query.edit_message_text(f"Unknown command: {data}")

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

async def handle_transaction_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle transaction ID input."""
    transaction_id = update.message.text
    amount = context.user_data.get('deposit_amount', 0)
    user_id = update.effective_user.id
    
    # Save deposit request to database
    db.add_deposit_request(user_id, amount, "generic", transaction_id)
    
    # Clear state
    context.user_data.pop('awaiting_input', None)
    context.user_data.pop('deposit_amount', None)
    
    await update.message.reply_text(
        "Your deposit request has been submitted and is pending admin approval. "
        "You will be notified once it's processed.",
        reply_markup=ReplyKeyboardMarkup([["🏠 Main Menu"]], resize_keyboard=True)
    )

async def show_balance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user balance."""
    user_id = update.effective_user.id
    balance = db.get_balance(user_id)
    await update.message.reply_text(f"💰 Your current balance: ৳{balance:.2f}")

async def show_support(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show support information."""
    support_text = """
    🆘 Support Center
    
    For any issues or questions, please contact:
    • @Admin1 (Primary)
    • @Admin2 (Secondary)
    
    ⏰ Response time: Within 24 hours
    💬 Please describe your issue in detail
    """
    await update.message.reply_text(support_text)

async def show_code_options(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show verification code options."""
    keyboard = [
        [
            InlineKeyboardButton("📧 Hotmail/Outlook Code", callback_data="code_hotmail"),
            InlineKeyboardButton("📨 Gmail Code", callback_data="code_gmail")
        ],
        [
            InlineKeyboardButton("🔗 External Code Links", callback_data="code_external"),
            InlineKeyboardButton("📋 Format Guide", callback_data="code_format")
        ],
        [
            InlineKeyboardButton("❓ Help Center", callback_data="code_help"),
            InlineKeyboardButton("🏠 Main Menu", callback_data="code_main_menu")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = """
    🔓 Get Verification Code
    
    Select the type of verification code you need:
    """
    
    await update.message.reply_text(text, reply_markup=reply_markup)

async def show_special_offers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show special offers."""
    offers_text = """
    ⭐ Special Offers
    
    🔥 Bulk Discounts:
    • 20+ pieces: 5% discount
    • 50+ pieces: 10% discount
    • 100+ pieces: 15% discount
    
    🎯 Regular Promotions:
    • Weekend specials
    • Holiday discounts
    • Referral bonuses
    
    💰 Save more when you buy in bulk!
    """
    await update.message.reply_text(offers_text)

async def show_referral_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show referral information."""
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    referral_text = f"""
    🎁 Bonus & Referral Program
    
    👥 Your Referrals: {user[6] if user else 0}
    💰 Your Earnings: ৳0.00 (Pending approval)
    
    🎯 Current Bonus Rates:
    • Referrer gets: ৳50.00
    • Referred user gets: ৳25.00
    
    🔗 Your Referral Link:
    https://t.me/your_bot_username?start=REF{user_id}
    
    📝 How it works:
    1. Share your referral link
    2. New users sign up using your link
    3. You both get bonuses!
    """
    await update.message.reply_text(referral_text)

async def process_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE, account_type: str, quantity: int) -> None:
    """Process account purchase."""
    query = update.callback_query
    user_id = update.effective_user.id
    price = db.get_price(account_type)
    total_cost = price * quantity
    balance = db.get_balance(user_id)
    
    if balance < total_cost:
        await query.edit_message_text(f"❌ Insufficient balance. You need ৳{total_cost:.2f} but have ৳{balance:.2f}.")
        return
    
    # Process purchase (would be implemented fully)
    db.update_balance(user_id, -total_cost)
    await query.edit_message_text(f"✅ Successfully purchased {quantity} {account_type} accounts for ৳{total_cost:.2f}!")

async def show_bulk_options(update: Update, context: ContextTypes.DEFAULT_TYPE, account_type: str) -> None:
    """Show bulk order options."""
    query = update.callback_query
    await query.edit_message_text("Bulk order options will be implemented soon.")

async def handle_hotmail_credentials(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle Hotmail credentials input."""
    # Implementation for Hotmail code retrieval
    await update.message.reply_text("Hotmail code service will be implemented soon.")

async def handle_gmail_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle Gmail email input."""
    # Implementation for Gmail code retrieval
    await update.message.reply_text("Gmail code service will be implemented soon.")

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
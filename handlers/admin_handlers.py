from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
import logging
import os
from config import ADMIN_IDS

logger = logging.getLogger(__name__)

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle document uploads for stock management."""
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ You are not authorized to upload files.")
        return
    
    if 'upload_service' not in context.user_data:
        await update.message.reply_text("❌ Please select an upload option first from the admin panel.")
        return
    
    service = context.user_data['upload_service']
    document = update.message.document
    
    # Check if file is Excel
    if not document.file_name.endswith(('.xlsx', '.xls')):
        await update.message.reply_text("❌ Please upload an Excel file (.xlsx or .xls).")
        return
    
    # Create data directory if it doesn't exist
    if not os.path.exists('data'):
        os.makedirs('data')
    
    # Download file
    file = await context.bot.get_file(document.file_id)
    file_path = f"data/{service}_data.xlsx"
    await file.download_to_drive(file_path)
    
    # Process file
    accounts_added = process_uploaded_file(file_path, service)
    
    await update.message.reply_text(
        f"✅ Successfully uploaded {accounts_added} {service} accounts."
    )
    
    # Clear upload state
    del context.user_data['upload_service']

async def handle_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle admin commands."""
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ You are not authorized to use admin commands.")
        return
    
    message_text = update.message.text
    
    if message_text == "⚡ Admin Panel":
        await show_admin_panel(update, context)
    elif message_text == "📤 Upload Hotmail":
        await prompt_upload_file(update, context, "hotmail")
    elif message_text == "📤 Upload Outlook":
        await prompt_upload_file(update, context, "outlook")
    elif message_text == "📤 Upload FB Gmail":
        await prompt_upload_file(update, context, "fb_gmail")
    elif message_text == "🏠 Main Menu":
        await show_user_main_menu(update, context)
    else:
        await update.message.reply_text("❌ Unknown admin command.")

async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show admin panel with options."""
    keyboard = [
        ["📤 Upload Hotmail", "📤 Upload Outlook", "📤 Upload FB Gmail"],
        ["🗑️ Remove Files", "🔄 Update Stocks", "💵 Set Prices"],
        ["📋 Pending Deposits", "📢 Broadcast", "👥 Manage Users"],
        ["🎯 Discount Settings", "🎁 Referral Settings", "⚙️ Settings"],
        ["🏠 Main Menu"]
    ]
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "👨‍💼 Admin Panel - Select an option:",
        reply_markup=reply_markup
    )

async def prompt_upload_file(update: Update, context: ContextTypes.DEFAULT_TYPE, service: str) -> None:
    """Prompt admin to upload a file for the specified service."""
    context.user_data['upload_service'] = service
    await update.message.reply_text(
        f"📤 Please upload the Excel file for {service} accounts.\n\n"
        f"✅ File should be in .xlsx format\n"
        f"✅ First row should contain headers\n"
        f"✅ Each row should contain account details"
    )

async def show_user_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user main menu."""
    from handlers.user_handlers import show_main_menu
    await show_main_menu(update, context)

def process_uploaded_file(file_path, service):
    """Process uploaded Excel file and return number of accounts added."""
    try:
        import openpyxl
        wb = openpyxl.load_workbook(file_path)
        ws = wb.active
        accounts_count = ws.max_row - 1  # Subtract header row
        return max(0, accounts_count)
    except Exception as e:
        logger.error(f"Error processing uploaded file: {e}")
        return 0

# Additional admin functions would be implemented here
async def remove_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove account files."""
    pass

async def update_stocks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Update stock counts."""
    pass

async def set_prices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set prices for accounts."""
    pass

async def manage_pending_deposits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manage pending deposits."""
    pass

async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Broadcast message to all users."""
    pass

async def manage_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manage users."""
    pass

async def discount_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Configure discount settings."""
    pass

async def referral_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Configure referral settings."""
    pass
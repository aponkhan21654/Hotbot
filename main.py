import os
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import BOT_TOKEN
from database import init_db
from handlers import start, error_handler, handle_callback_query, handle_message, handle_document
from handlers import set_price_command, approve_deposit_command, reject_deposit_command
from handlers import add_discount_command, remove_discount_command, set_referral_command

def main():
    # Initialize database
    init_db()
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("setprice", set_price_command))
    application.add_handler(CommandHandler("approve", approve_deposit_command))
    application.add_handler(CommandHandler("reject", reject_deposit_command))
    application.add_handler(CommandHandler("adddiscount", add_discount_command))
    application.add_handler(CommandHandler("removediscount", remove_discount_command))
    application.add_handler(CommandHandler("setreferral", set_referral_command))
    
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    
    application.add_error_handler(error_handler)
    
    # Create xlsx_files directory if it doesn't exist
    if not os.path.exists('xlsx_files'):
        os.makedirs('xlsx_files')
    
    # Create empty Excel files if they don't exist
    from config import SERVICE_FILES
    from openpyxl import Workbook
    
    for service, filename in SERVICE_FILES.items():
        if not os.path.exists(filename):
            wb = Workbook()
            ws = wb.active
            if service == 'hotmail':
                ws.append(['Email', 'Password', 'Recovery Email', 'Phone'])
            elif service == 'outlook':
                ws.append(['Email', 'Password', 'First Name', 'Last Name', 'Country'])
            elif service == 'fb_gmail':
                ws.append(['Email', 'Password', 'Recovery Email', 'DOB'])
            wb.save(filename)
    
    # Start the bot
    print("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
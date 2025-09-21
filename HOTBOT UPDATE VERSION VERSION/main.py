import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from config import BOT_TOKEN, ADMIN_IDS
from database import Database
import handlers.user_handlers as user_handlers
import handlers.admin_handlers as admin_handlers
import handlers.payment_handlers as payment_handlers

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

def main() -> None:
    """Start the bot."""
    # Initialize database
    db = Database("bot_database.db")
    
    # Create the Application and pass it your bot's token
    application = Application.builder().token(BOT_TOKEN).build()

    # Add handlers for commands
    application.add_handler(CommandHandler("start", user_handlers.start))
    
    # Add handler for messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, user_handlers.handle_message))
    
    # Add handler for document uploads (for admin stock management)
    application.add_handler(MessageHandler(filters.Document.ALL, admin_handlers.handle_document))
    
    # Add handler for callback queries (inline keyboard buttons)
    application.add_handler(CallbackQueryHandler(user_handlers.handle_callback_query))
    
    # Run the bot until you press Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()

import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(id) for id in os.getenv("ADMIN_IDS", "").split(",") if id]
DATABASE_NAME = "bot_database.db"

# API endpoints
HOTMAIL_API = "https://hsmail.shop/api2.php"
GMAIL_API = "https://hsmail.shop/api.php"

# Default prices (can be changed via admin panel)
DEFAULT_PRICES = {
    "hotmail": 10.0,
    "outlook": 10.0,
    "fb_gmail": 10.0
}

# Default referral bonuses
REFERRAL_BONUS = {
    "referrer": 50.0,
    "referred": 25.0
}

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from database import get_stock_count, get_price, get_discount_settings, get_referral_settings
from config import SERVICE_NAMES, SERVICE_FILES, ADMIN_IDS

def get_main_keyboard(user_id: int):
    """Get main keyboard based on user role"""
    is_admin = user_id in ADMIN_IDS
    items = []
    
    # Common buttons for all users
    items.append(["Buy Accounts", "Get Code"])
    items.append(["Balance", "Deposit"])
    items.append(["Referral", "Special Offers"])
    items.append(["Support", "About"])
    
    # Admin-only buttons
    if is_admin:
        items.append(["Admin Panel"])
    
    return ReplyKeyboardMarkup(items, resize_keyboard=True)

def get_admin_panel_keyboard():
    """Get admin panel keyboard"""
    return ReplyKeyboardMarkup([
        ["Upload Hotmail", "Upload Outlook", "Upload FB Gmail"],
        ["Remove Files", "Update Stocks"],
        ["Set Prices", "Pending Deposits"],
        ["Broadcast", "Manage Users"],
        ["Discount Settings", "Referral Settings", "Settings", "Main Menu"]
    ], resize_keyboard=True)

def get_remove_files_keyboard():
    """Get remove files keyboard"""
    return ReplyKeyboardMarkup([
        ["Remove Hotmail", "Remove Outlook", "Remove FB Gmail"],
        ["Back to Admin Panel"]
    ], resize_keyboard=True)

def get_broadcast_keyboard():
    """Get broadcast keyboard"""
    return ReplyKeyboardMarkup([
        ["Confirm Broadcast", "Edit Message"],
        ["Cancel Broadcast"]
    ], resize_keyboard=True)

def get_deposit_method_keyboard():
    """Get deposit method keyboard"""
    return ReplyKeyboardMarkup([
        ["BKash", "Nagad", "Rocket"],
        ["Bank Transfer", "Card"],
        ["Cancel"]
    ], resize_keyboard=True)

def get_service_buy_keyboard(service_key: str):
    """Get service buy keyboard"""
    keyboard = []
    stock_count = get_stock_count(service_key)
    price = get_price(service_key)
    
    keyboard.append([f"Buy {SERVICE_NAMES.get(service_key, service_key)} - ${price}"])
    keyboard.append([f"Stock: {stock_count} available"])
    keyboard.append(["Back to Services"])
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_code_menu_keyboard():
    """Get code menu keyboard"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Hotmail/Outlook Code", callback_data='get_hotmail_code')],
        [InlineKeyboardButton("Gmail Code", callback_data='get_gmail_code')],
        [InlineKeyboardButton("External Code Links", callback_data='code_links')],
        [InlineKeyboardButton("Format Guide", callback_data='show_format')],
        [InlineKeyboardButton("Help Center", callback_data='code_help')],
        [InlineKeyboardButton("Main Menu", callback_data='main_menu')]
    ])

def get_code_action_keyboard(service_type: str, is_error: bool = False):
    """Get code action keyboard"""
    buttons = []
    
    if is_error:
        buttons.append([InlineKeyboardButton("Try Again", callback_data=f'retry_{service_type}')])
        buttons.append([InlineKeyboardButton("Contact Support", callback_data='contact_support')])
    else:
        buttons.append([InlineKeyboardButton("Get Another Code", callback_data=f'get_{service_type}_code')])
    
    buttons.append([InlineKeyboardButton("Main Menu", callback_data='main_menu')])
    
    return InlineKeyboardMarkup(buttons)

def get_code_links_keyboard():
    """Get code links keyboard"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Hotmail/Outlook Code Service", url="https://dongvanfb.net/read_mail_box/")],
        [InlineKeyboardButton("Premium Gmail Code (Tridib)", url="https://tridib.codes")],
        [InlineKeyboardButton("VIP Gmail Code (Abmeta)", url="https://abmeta.store")],
        [InlineKeyboardButton("Back to Code Menu", callback_data='get_code_menu')]
    ])

def get_discount_settings_keyboard():
    """Get discount settings keyboard"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("View Discounts", callback_data='view_discounts')],
        [InlineKeyboardButton("Add Discount", callback_data='add_discount')],
        [InlineKeyboardButton("Edit Discount", callback_data='edit_discount')],
        [InlineKeyboardButton("Remove Discount", callback_data='remove_discount')],
        [InlineKeyboardButton("Back to Admin", callback_data='back_to_admin')]
    ])

def get_referral_settings_keyboard():
    """Get referral settings keyboard"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("View Settings", callback_data='view_referral_settings')],
        [InlineKeyboardButton("Edit Settings", callback_data='edit_referral_settings')],
        [InlineKeyboardButton("Back to Admin", callback_data='back_to_admin')]
    ])

def get_manage_users_keyboard():
    """Get manage users keyboard"""
    return ReplyKeyboardMarkup([
        ["Add Balance", "Send Message"],
        ["View User Info", "Cancel"]
    ], resize_keyboard=True)
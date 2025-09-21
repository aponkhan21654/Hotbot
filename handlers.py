import os
import re
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from functools import wraps

from config import BOT_TOKEN, ADMIN_IDS, SUPPORT_CONTACTS, HOTMAIL_API_URL, GMAIL_API_URL
from config import SERVICE_NAMES, SERVICE_FILES, CODE_FORMATS
from database import init_db, get_user_data, create_user, update_user_balance, get_balance, get_price, set_price
from database import get_discount_settings, update_discount_settings, remove_discount_setting, get_referral_settings
from database import update_referral_settings_db, save_deposit_request, update_deposit_transaction_id
from database import process_deposit_decision_db, get_pending_deposits, get_all_user_ids, save_broadcast_message_db
from database import update_broadcast_count_db
from keyboards import get_main_keyboard, get_admin_panel_keyboard, get_remove_files_keyboard, get_broadcast_keyboard
from keyboards import get_deposit_method_keyboard, get_service_buy_keyboard, get_code_menu_keyboard
from keyboards import get_code_action_keyboard, get_code_links_keyboard, get_discount_settings_keyboard
from keyboards import get_referral_settings_keyboard, get_manage_users_keyboard
from utils import admin_only, user_sessions, session_timeouts, clear_user_session, set_session_timeout
from utils import get_stock_count, get_rows_for_purchase, remove_purchased_rows, append_excel_data
from utils import create_user_download_file, calculate_discount, fetch_code_from_api
from utils import generate_referral_code, get_or_create_referral_code, get_referral_link, handle_referral_signup
from utils import get_referral_stats

logger = logging.getLogger(__name__)

# Core Handlers
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors in the bot"""
    logger.error(f"Error occurred for update {update}: {context.error}", exc_info=True)
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text("  error      ")
        except Exception as e:
            logger.error(f"Failed to send error message: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command"""
    user_id = update.effective_user.id
    username = update.effective_user.username or f"User_{user_id}"
    create_user(user_id, username)
    
    # Check if this is a referral start
    if context.args and len(context.args) > 0:
        referral_code = context.args[0]
        if referral_code.startswith('REF'):
            handle_referral_signup(user_id, referral_code)
    
    welcome_message = f""" Welcome to Account Verification Bot, {update.effective_user.first_name}! 

   :
 Hotmail -   
 Outlook -   
 FB Gmail - VIP FB  
 Get Code -  Verification code

  :
 24/7  
 100%  
  
 100% 

     Deposit   
    Support   """
    
    await update.message.reply_text(welcome_message, parse_mode='Markdown', reply_markup=get_main_keyboard(user_id))

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries from inline keyboards"""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    
    if data == 'main_menu':
        await query.message.reply_text(" Main Menu", reply_markup=get_main_keyboard(user_id))
    
    elif data == 'get_code_menu':
        code_menu_message = " Get Code Menu\n\nChoose an option below to get verification codes:"
        await query.message.reply_text(code_menu_message, reply_markup=get_code_menu_keyboard())
    
    elif data in ['get_hotmail_code', 'get_gmail_code']:
        service_type = 'hotmail' if data == 'get_hotmail_code' else 'gmail'
        format_text = CODE_FORMATS[service_type]
        timeout_minutes = 15 if service_type == 'hotmail' else 10
        
        # Generate a session code
        session_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        user_sessions[user_id] = {
            'service_type': service_type,
            'session_code': session_code,
            'created_at': datetime.now()
        }
        
        # Set session timeout
        await set_session_timeout(user_id, context, timeout_minutes)
        
        format_message = f""" {SERVICE_NAMES.get(service_type, service_type).upper()} Format Guide

{format_text}

Example: {'example@outlook.com|yourpassword|yourtoken|yourclientid' if service_type == 'hotmail' else 'example@gmail.com'}

 Your Session Code: {session_code}
Session expires in {timeout_minutes} minutes

 Tips:  credentials    {timeout_minutes} minutes   code receive """
        await query.message.reply_text(format_message, parse_mode='Markdown')
    
    elif data == 'code_links':
        links_message = " External Code Services\n\nHere are some trusted external code services:"
        await query.message.reply_text(links_message, reply_markup=get_code_links_keyboard())
    
    elif data == 'show_format':
        format_message = f""" Code Format Guide

Hotmail/Outlook Format: {CODE_FORMATS['hotmail']}

Gmail Format: {CODE_FORMATS['gmail']}

 Note: Hotmail/Outlook    information  , Gmail    email"""
        await query.message.reply_text(format_message, parse_mode='Markdown')
    
    elif data == 'code_help':
        help_message = f""" Code Help Center

1. How to get codes?
   ú Get Code   
   ú   service select 
   ú Provided format  credentials send 
   ú Bot automatically code fetch 
2. Session timeout?
   ú Hotmail/Outlook: 15 minutes
   ú Gmail: 10 minutes
3. Credentials safe?
   ú  100% secure and encrypted
   ú  Only used for code retrieval
   ú  Never stored permanently
4. Not getting codes?
   ú Check your credentials
   ú Ensure you have active codes
   ú Contact support if needed

 Support: {', '.join(SUPPORT_CONTACTS)}"""
        await query.message.reply_text(help_message, parse_mode='Markdown')
    
    elif data.startswith('retry_'):
        service_type = data.split('_')[1]
        format_text = CODE_FORMATS[service_type]
        timeout_minutes = 15 if service_type == 'hotmail' else 10
        
        # Generate a new session code
        session_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        user_sessions[user_id] = {
            'service_type': service_type,
            'session_code': session_code,
            'created_at': datetime.now()
        }
        
        # Set session timeout
        await set_session_timeout(user_id, context, timeout_minutes)
        
        format_message = f""" Retry Session

 Format: {format_text}

 Your New Session Code: {session_code}
Session expires in {timeout_minutes} minutes

Please send your credentials in the correct format."""
        await query.message.reply_text(format_message, parse_mode='Markdown')
    
    elif data == 'contact_support':
        support_message = f""" Contact Support

For assistance, please contact our support team:
{', '.join(SUPPORT_CONTACTS)}

We're here to help you 24/7!"""
        await query.message.reply_text(support_message, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all incoming messages"""
    user_id = update.effective_user.id
    text = update.message.text
    
    # Check if user is in a session for code retrieval
    if user_id in user_sessions:
        session_data = user_sessions[user_id]
        service_type = session_data['service_type']
        
        # Validate the format based on service type
        if service_type == 'hotmail':
            # Expected format: email|password|token|client_id
            if not re.match(r'^[^|]+\|[^|]+\|[^|]+\|[^|]+$', text):
                error_msg = " Invalid Format\n\nPlease use the format: email|password|token|client_id"
                await update.message.reply_text(error_msg, reply_markup=get_code_action_keyboard(service_type, True))
                return
            
            # Extract credentials
            email, password, token, client_id = text.split('|')
            
            # Show checking message
            checking_msg = f""" Email: {email}
Checking for verification codes via API... Please wait while I fetch the latest verification code.This may take a few moments."""
            await update.message.reply_text(checking_msg)
            
            # Call API to get code
            params = {
                'email': email,
                'password': password,
                'token': token,
                'client_id': client_id
            }
            code, api_response = await fetch_code_from_api(HOTMAIL_API_URL, params)
            
            if code:
                # Success - send the code
                success_msg = f""" Email: {email}
Verification Code: {code}
Code Validity: 10 minutes
Tips: Use this code immediately as it will expire soon.
Security Note: Never share this code with anyone."""
                await update.message.reply_text(success_msg, reply_markup=get_code_action_keyboard(service_type))
            else:
                # Error - show error message
                error_msg = api_response.get('message', 'Unknown error occurred')
                error_response = f""" Error: {error_msg}

Possible reasons:

1.  No recent codes received
2.  Incorrect credentials
3.  Account security issues
4.  API temporary issue

Please make sure:
You have received a code recently
Your credentials are correct
Your account is accessible"""
                await update.message.reply_text(error_response, reply_markup=get_code_action_keyboard(service_type, True))
        
        elif service_type == 'gmail':
            # Expected format: email
            if not re.match(r'^[a-zA-Z0-9._%+-]+@gmail\.com$', text):
                error_msg = " Invalid Format\n\nPlease provide a valid Gmail address"
                await update.message.reply_text(error_msg, reply_markup=get_code_action_keyboard(service_type, True))
                return
            
            email = text
            
            # Show checking message
            checking_msg = f""" Email: {email}
Checking for Gmail codes via API... Please wait while I fetch the latest Gmail verification code."""
            await update.message.reply_text(checking_msg)
            
            # Call API to get code
            params = {'email': email}
            code, api_response = await fetch_code_from_api(GMAIL_API_URL, params)
            
            if code:
                # Success - send the code
                success_msg = f""" Email: {email}
Verification Code: {code}
Code Validity: 10 minutes
Tips: Use this code immediately for verification.
Security Note: Protect your code and never share it."""
                await update.message.reply_text(success_msg, reply_markup=get_code_action_keyboard(service_type))
            else:
                # Error - show error message
                error_msg = api_response.get('message', 'Unknown error occurred')
                error_response = f"""There was an error accessing your messages. This could be due to:

1.  Network issues
2.  API temporary downtime
3.  Account security restrictions
4.  Invalid credentials

Please try again later or contact support if the issue persists."""
                await update.message.reply_text(error_response, reply_markup=get_code_action_keyboard(service_type, True))
        
        # Clear the session after processing
        clear_user_session(user_id)
        return
    
    # Handle menu options
    if text == " Buy Accounts":
        services_message = " Buy Accounts\n\nChoose an account type to purchase:"
        keyboard = [
            [SERVICE_NAMES['hotmail'], SERVICE_NAMES['outlook']],
            [SERVICE_NAMES['fb_gmail'], " Back"]
        ]
        await update.message.reply_text(services_message, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    
    elif text in SERVICE_NAMES.values():
        # Find the service key from the name
        service_key = None
        for key, name in SERVICE_NAMES.items():
            if name == text:
                service_key = key
                break
        
        if service_key:
            await update.message.reply_text(
                f"{text} Account Purchase", 
                reply_markup=get_service_buy_keyboard(service_key)
            )
    
    elif text == " Get Code":
        code_menu_message = " Get Code Menu\n\nChoose an option below to get verification codes:"
        await update.message.reply_text(code_menu_message, reply_markup=get_code_menu_keyboard())
    
    elif text == " Balance":
        balance = get_balance(user_id)
        await update.message.reply_text(f" Your Current Balance: {balance:.2f}")
    
    elif text == " Deposit":
        deposit_message = """ Deposit Funds

Choose a deposit method:"""
        await update.message.reply_text(deposit_message, reply_markup=get_deposit_method_keyboard())
    
    elif text in [" BKash", " Nagad", " Rocket", " Bank Transfer", " Card"]:
        method = text.replace(" ", "").replace(" ", "").replace(" ", "").replace(" ", "").replace(" ", "")
        await update.message.reply_text(f"Please send the amount you want to deposit via {method}.")
        # Store the deposit method in context for the next message
        context.user_data['deposit_method'] = method
    
    elif text == " Referral":
        stats = get_referral_stats(user_id)
        referral_link = get_referral_link(user_id, context.bot.username)
        
        referral_message = f""" Your Referral Stats:
 Total Referrals: {stats['total_refs']}
 Total Earnings: {stats['total_earnings']:.2f}
 Pending Rewards: {stats['pending_rewards']}

Bonus Rates:
 You earn: {stats['referrer_bonus']:.2f} per referral
 Friend gets: {stats['referred_bonus']:.2f} welcome bonus

Your Referral Link: {referral_link}

How it works:

1. Share your referral link with friends
2. When they join using your link, you get {stats['referrer_bonus']:.2f} bonus
3. They also get {stats['referred_bonus']:.2f} welcome bonus
4. Earn unlimited rewards!

Pro Tip: Share your link in groups and social media to earn more!"""
        await update.message.reply_text(referral_message, parse_mode='Markdown')
    
    elif text == " Special Offers":
        discounts = get_discount_settings()
        discount_text = "\n".join([f" {qty}+ pieces: {discount}% discount" for qty, discount in discounts]) if discounts else "No current discounts"
        
        offers_message = f""" Special Offers

{discount_text}

 Buy more, save more!"""
        await update.message.reply_text(offers_message, parse_mode='Markdown')
    
    elif text == " Support":
        support_message = f""" Support

For any assistance, please contact our support team:
Support Contacts:"""
        for support_id in SUPPORT_CONTACTS:
            support_message += f"\n {support_id}"
        
        support_message += """

 24/7 Support: Yes
We're here to help you!"""
        await update.message.reply_text(support_message, parse_mode='Markdown')
    
    elif text == " About":
        about_message = """ About Account Verification Bot

We provide premium accounts and verification codes for:
 Hotmail Accounts
 Outlook Accounts
 FB Gmail Accounts
 Verification Codes

 Features:
 24/7 Active Service
 100% Guaranteed Accounts
 Fast Delivery
 100% Secure

Contact our support for any questions!"""
        await update.message.reply_text(about_message, parse_mode='Markdown')
    
    elif text == " Admin Panel" and user_id in ADMIN_IDS:
        await update.message.reply_text(" Admin Panel", reply_markup=get_admin_panel_keyboard())
    
    elif text == " Main Menu":
        await update.message.reply_text(" Main Menu", reply_markup=get_main_keyboard(user_id))
    
    elif text == " Back to Services":
        services_message = " Buy Accounts\n\nChoose an account type to purchase:"
        keyboard = [
            [SERVICE_NAMES['hotmail'], SERVICE_NAMES['outlook']],
            [SERVICE_NAMES['fb_gmail'], " Back"]
        ]
        await update.message.reply_text(services_message, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    
    elif text == " Back":
        await update.message.reply_text(" Main Menu", reply_markup=get_main_keyboard(user_id))
    
    elif text == " Back to Admin Panel":
        await update.message.reply_text(" Admin Panel", reply_markup=get_admin_panel_keyboard())
    
    elif text == " Cancel":
        await update.message.reply_text(" Main Menu", reply_markup=get_main_keyboard(user_id))
    
    # Handle admin commands
    elif text.startswith(" Upload ") and user_id in ADMIN_IDS:
        service = text.replace(" Upload ", "").lower()
        if service in SERVICE_NAMES:
            await update.message.reply_text(f"Please send the Excel file for {SERVICE_NAMES[service]} accounts.")
            context.user_data['upload_service'] = service
    
    elif text.startswith(" Remove ") and user_id in ADMIN_IDS:
        service = text.replace(" Remove ", "").lower()
        if service in SERVICE_NAMES:
            # Remove the file
            filename = SERVICE_FILES.get(service)
            if os.path.exists(filename):
                os.remove(filename)
                await update.message.reply_text(f" {SERVICE_NAMES[service]} file removed successfully.")
            else:
                await update.message.reply_text(f" {SERVICE_NAMES[service]} file does not exist.")
    
    elif text == " Update Stocks" and user_id in ADMIN_IDS:
        stocks_message = " Current Stocks:\n"
        for service, name in SERVICE_NAMES.items():
            stock_count = get_stock_count(service)
            stocks_message += f" {name}: {stock_count} accounts\n"
        
        await update.message.reply_text(stocks_message, parse_mode='Markdown')
    
    elif text == " Set Prices" and user_id in ADMIN_IDS:
        prices_message = " Current Prices:\n"
        for service, name in SERVICE_NAMES.items():
            price = get_price(service)
            prices_message += f" {name}: {price:.2f}\n"
        
        prices_message += "\nTo set a new price, use the format: /setprice service price\nExample: /setprice hotmail 50"
        await update.message.reply_text(prices_message, parse_mode='Markdown')
    
    elif text == " Pending Deposits" and user_id in ADMIN_IDS:
        pending_deposits = get_pending_deposits()
        if not pending_deposits:
            await update.message.reply_text(" No pending deposits.")
        else:
            deposits_message = " Pending Deposits:\n\n"
            for deposit in pending_deposits:
                deposits_message += f"ID: {deposit[0]}\nUser: {deposit[2]} (ID: {deposit[1]})\nAmount: {deposit[3]:.2f}\nMethod: {deposit[4]}\nTxn ID: {deposit[5] or 'Not provided'}\n\n"
            
            deposits_message += "Use /approve id or /reject id to process deposits."
            await update.message.reply_text(deposits_message, parse_mode='Markdown')
    
    elif text == " Broadcast" and user_id in ADMIN_IDS:
        await update.message.reply_text(" Broadcast Message\n\nPlease send the message you want to broadcast to all users.", reply_markup=get_broadcast_keyboard())
        context.user_data['broadcast_mode'] = True
    
    elif text == " Manage Users" and user_id in ADMIN_IDS:
        await update.message.reply_text(" User Management\n\nChoose an action:", reply_markup=get_manage_users_keyboard())
    
    elif text == " Discount Settings" and user_id in ADMIN_IDS:
        await update.message.reply_text(" Discount Settings\n\nManage quantity discounts:", reply_markup=get_discount_settings_keyboard())
    
    elif text == " Referral Settings" and user_id in ADMIN_IDS:
        await update.message.reply_text(" Referral Settings\n\nManage referral bonuses:", reply_markup=get_referral_settings_keyboard())
    
    elif text == " Settings" and user_id in ADMIN_IDS:
        await update.message.reply_text(" Bot Settings\n\nConfigure your bot settings:\n\n  Price Management\n  Stock Management\n  User Management\n  Broadcast Settings\n  Discount Settings\n  Referral Settings\n\nUse the Admin Panel for all settings.", parse_mode='Markdown', reply_markup=get_admin_panel_keyboard())
    
    elif text == " Confirm Broadcast" and user_id in ADMIN_IDS and 'broadcast_message' in context.user_data:
        message_text = context.user_data['broadcast_message']
        broadcast_id = save_broadcast_message_db(user_id, message_text)
        
        # Get all user IDs
        all_user_ids = get_all_user_ids()
        sent_count = 0
        
        # Send broadcast to all users
        for uid in all_user_ids:
            try:
                await context.bot.send_message(chat_id=uid, text=message_text)
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send broadcast to user {uid}: {e}")
        
        # Update broadcast count
        update_broadcast_count_db(broadcast_id, sent_count)
        
        await update.message.reply_text(f" Broadcast sent to {sent_count} users.", reply_markup=get_admin_panel_keyboard())
        del context.user_data['broadcast_message']
        del context.user_data['broadcast_mode']
    
    elif text == " Edit Message" and user_id in ADMIN_IDS and 'broadcast_mode' in context.user_data:
        await update.message.reply_text("Please send the updated broadcast message.")
    
    elif text == " Cancel Broadcast" and user_id in ADMIN_IDS and 'broadcast_mode' in context.user_data:
        await update.message.reply_text(" Broadcast cancelled.", reply_markup=get_admin_panel_keyboard())
        if 'broadcast_message' in context.user_data:
            del context.user_data['broadcast_message']
        del context.user_data['broadcast_mode']
    
    elif text == " Add Balance" and user_id in ADMIN_IDS:
        await update.message.reply_text("Please send the user ID and amount in the format: user_id amount\nExample: 123456789 100.50")
        context.user_data['add_balance_mode'] = True
    
    elif text == " Send Message" and user_id in ADMIN_IDS:
        await update.message.reply_text("Please send the user ID and message in the format: user_id message\nExample: 123456789 Hello, how are you?")
        context.user_data['send_message_mode'] = True
    
    elif text == " View User Info" and user_id in ADMIN_IDS:
        await update.message.reply_text("Please send the user ID to view information.")
        context.user_data['view_user_mode'] = True
    
    else:
        # Handle deposit amount input
        if 'deposit_method' in context.user_data:
            try:
                amount = float(text)
                if amount <= 0:
                    await update.message.reply_text(" Amount must be greater than 0.")
                    return
                
                method = context.user_data['deposit_method']
                save_deposit_request(user_id, amount, method)
                
                await update.message.reply_text(
                    f" Deposit request submitted!\n\n"
                    f"Amount: {amount:.2f}\n"
                    f"Method: {method}\n\n"
                    f"Please send the amount to our {method} account and reply with your transaction ID.\n\n"
                    f"Your request will be processed within 24 hours."
                )
                
                # Ask for transaction ID
                await update.message.reply_text("Please send your transaction ID:")
                context.user_data['awaiting_transaction_id'] = True
                
            except ValueError:
                await update.message.reply_text(" Please enter a valid amount.")
        
        # Handle transaction ID input
        elif 'awaiting_transaction_id' in context.user_data:
            # Get the latest deposit request for this user
            from database import db_execute
            latest_request = db_execute(
                'SELECT id FROM deposit_requests WHERE user_id = ? ORDER BY id DESC LIMIT 1', 
                (user_id,), 
                fetchone=True
            )
            
            if latest_request:
                request_id = latest_request[0]
                update_deposit_transaction_id(request_id, text)
                await update.message.reply_text(
                    " Transaction ID recorded!\n\n"
                    "Your deposit request is now pending approval.\n"
                    "You will be notified once it's processed."
                )
                
                # Notify admins
                for admin_id in ADMIN_IDS:
                    try:
                        await context.bot.send_message(
                            chat_id=admin_id,
                            text=f" New Deposit Request\n\n"
                                 f"User: {update.effective_user.username or update.effective_user.first_name} (ID: {user_id})\n"
                                 f"Amount: {context.user_data.get('deposit_amount', 0):.2f}\n"
                                 f"Method: {context.user_data.get('deposit_method', 'Unknown')}\n"
                                 f"Transaction ID: {text}\n\n"
                                 f"Use /approve {request_id} or /reject {request_id} to process."
                        )
                    except Exception as e:
                        logger.error(f"Failed to notify admin {admin_id}: {e}")
            
            # Clean up
            if 'deposit_method' in context.user_data:
                del context.user_data['deposit_method']
            if 'deposit_amount' in context.user_data:
                del context.user_data['deposit_amount']
            if 'awaiting_transaction_id' in context.user_data:
                del context.user_data['awaiting_transaction_id']
        
        # Handle broadcast message input
        elif 'broadcast_mode' in context.user_data:
            context.user_data['broadcast_message'] = text
            await update.message.reply_text(
                f" Broadcast Message Preview:\n\n{text}\n\n"
                f"Recipients: {len(get_all_user_ids())} users\n\n"
                f"Please confirm to send this message to all users.",
                reply_markup=get_broadcast_keyboard()
            )
        
        # Handle add balance input
        elif 'add_balance_mode' in context.user_data:
            try:
                parts = text.split()
                if len(parts) < 2:
                    await update.message.reply_text(" Please provide both user ID and amount.")
                    return
                
                target_user_id = int(parts[0])
                amount = float(parts[1])
                
                update_user_balance(target_user_id, amount)
                
                await update.message.reply_text(f" Added {amount:.2f} to user {target_user_id}'s balance.")
                
                # Notify the user
                try:
                    await context.bot.send_message(
                        chat_id=target_user_id,
                        text=f" Admin has added {amount:.2f} to your balance.\n\nYour new balance: {get_balance(target_user_id):.2f}"
                    )
                except Exception as e:
                    logger.error(f"Failed to notify user {target_user_id}: {e}")
                
                del context.user_data['add_balance_mode']
                
            except (ValueError, IndexError):
                await update.message.reply_text(" Invalid format. Please use: user_id amount\nExample: 123456789 100.50")
        
        # Handle send message input
        elif 'send_message_mode' in context.user_data:
            try:
                parts = text.split(' ', 1)
                if len(parts) < 2:
                    await update.message.reply_text(" Please provide both user ID and message.")
                    return
                
                target_user_id = int(parts[0])
                message = parts[1]
                
                # Send message to the user
                try:
                    await context.bot.send_message(
                        chat_id=target_user_id,
                        text=f" Message from Admin:\n\n{message}"
                    )
                    await update.message.reply_text(f" Message sent to user {target_user_id}.")
                except Exception as e:
                    await update.message.reply_text(f" Failed to send message to user {target_user_id}: {e}")
                
                del context.user_data['send_message_mode']
                
            except ValueError:
                await update.message.reply_text(" Invalid format. Please use: user_id message\nExample: 123456789 Hello, how are you?")
        
        # Handle view user info input
        elif 'view_user_mode' in context.user_data:
            try:
                target_user_id = int(text)
                user_data = get_user_data(target_user_id)
                
                if user_data:
                    user_info = f""" User Information

User ID: {user_data[0]}
Username: {user_data[1]}
Balance: {user_data[2]:.2f}
Referral Code: {user_data[3]}
Referred By: {user_data[4] or 'None'}
Total Referrals: {user_data[5]}"""
                    await update.message.reply_text(user_info, parse_mode='Markdown')
                else:
                    await update.message.reply_text(" User not found.")
                
                del context.user_data['view_user_mode']
                
            except ValueError:
                await update.message.reply_text(" Please provide a valid user ID.")
        
        else:
            await update.message.reply_text(" Invalid Command\n\nPlease select a valid option from the menu:", parse_mode='Markdown', reply_markup=get_main_keyboard(user_id))

# Admin command handlers
@admin_only
async def set_price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set price for a service"""
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(" Usage: /setprice <service> <price>\nExample: /setprice hotmail 50")
        return
    
    service = context.args[0].lower()
    try:
        price = float(context.args[1])
        if service not in SERVICE_NAMES:
            await update.message.reply_text(f" Invalid service. Available services: {', '.join(SERVICE_NAMES.keys())}")
            return
        
        set_price(service, price)
        await update.message.reply_text(f" Price for {SERVICE_NAMES[service]} set to {price:.2f}")
    except ValueError:
        await update.message.reply_text(" Please provide a valid price.")

@admin_only
async def approve_deposit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Approve a deposit request"""
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(" Usage: /approve <request_id>")
        return
    
    try:
        request_id = int(context.args[0])
        user_id, amount = process_deposit_decision_db(request_id, 'approved')
        
        if user_id and amount:
            await update.message.reply_text(f" Deposit request #{request_id} approved. {amount:.2f} added to user {user_id}'s balance.")
            
            # Notify the user
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f" Your deposit of {amount:.2f} has been approved.\n\nYour new balance: {get_balance(user_id):.2f}"
                )
            except Exception as e:
                logger.error(f"Failed to notify user {user_id}: {e}")
        else:
            await update.message.reply_text(f" Deposit request #{request_id} not found or already processed.")
    except ValueError:
        await update.message.reply_text(" Please provide a valid request ID.")

@admin_only
async def reject_deposit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reject a deposit request"""
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(" Usage: /reject <request_id>")
        return
    
    try:
        request_id = int(context.args[0])
        user_id, amount = process_deposit_decision_db(request_id, 'rejected')
        
        if user_id:
            await update.message.reply_text(f" Deposit request #{request_id} rejected.")
            
            # Notify the user
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f" Your deposit request of {amount:.2f} has been rejected.\n\nPlease contact support if you believe this is an error."
                )
            except Exception as e:
                logger.error(f"Failed to notify user {user_id}: {e}")
        else:
            await update.message.reply_text(f" Deposit request #{request_id} not found or already processed.")
    except ValueError:
        await update.message.reply_text(" Please provide a valid request ID.")

@admin_only
async def add_discount_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add a discount setting"""
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(" Usage: /adddiscount <min_quantity> <discount_percent>\nExample: /adddiscount 10 5")
        return
    
    try:
        min_quantity = int(context.args[0])
        discount_percent = float(context.args[1])
        
        update_discount_settings(min_quantity, discount_percent)
        await update.message.reply_text(f" Discount added: {min_quantity}+ pieces = {discount_percent}% discount")
    except ValueError:
        await update.message.reply_text(" Please provide valid numbers.")

@admin_only
async def remove_discount_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove a discount setting"""
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(" Usage: /removediscount <min_quantity>\nExample: /removediscount 10")
        return
    
    try:
        min_quantity = int(context.args[0])
        remove_discount_setting(min_quantity)
        await update.message.reply_text(f" Discount for {min_quantity}+ pieces removed.")
    except ValueError:
        await update.message.reply_text(" Please provide a valid quantity.")

@admin_only
async def set_referral_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set referral bonuses"""
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(" Usage: /setreferral <referrer_bonus> <referred_bonus>\nExample: /setreferral 50 25")
        return
    
    try:
        referrer_bonus = float(context.args[0])
        referred_bonus = float(context.args[1])
        
        update_referral_settings_db(referrer_bonus, referred_bonus)
        await update.message.reply_text(f" Referral bonuses updated:\n Referrer gets: {referrer_bonus:.2f}\n Referred gets: {referred_bonus:.2f}")
    except ValueError:
        await update.message.reply_text(" Please provide valid bonus amounts.")

# File handler for admin uploads
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle document uploads for admin"""
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text(" Access denied. Admin only feature.")
        return
    
    if 'upload_service' not in context.user_data:
        await update.message.reply_text(" Please use the admin panel to upload files.")
        return
    
    service = context.user_data['upload_service']
    document = update.message.document
    
    # Check if it's an Excel file
    if not document.file_name.endswith(('.xlsx', '.xls')):
        await update.message.reply_text(" Please upload an Excel file (.xlsx or .xls).")
        return
    
    # Download the file
    file = await context.bot.get_file(document.file_id)
    filename = SERVICE_FILES[service]
    
    try:
        await file.download_to_drive(filename)
        stock_count = get_stock_count(service)
        await update.message.reply_text(f" {SERVICE_NAMES[service]} file uploaded successfully.\n Current stock: {stock_count} accounts.")
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        await update.message.reply_text(" Error uploading file. Please try again.")
    
    # Clean up
    del context.user_data['upload_service']
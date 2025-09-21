import sqlite3
import logging
from datetime import datetime
import random
import string

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_name):
        self.db_name = db_name
        self.init_db()
    
    def get_connection(self):
        return sqlite3.connect(self.db_name)
    
    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                balance REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                referral_code TEXT UNIQUE,
                referred_by INTEGER,
                total_referrals INTEGER DEFAULT 0,
                FOREIGN KEY (referred_by) REFERENCES users (user_id)
            )
        ''')
        
        # Prices table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prices (
                service TEXT PRIMARY KEY,
                price REAL
            )
        ''')
        
        # Deposit requests table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS deposit_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount REAL,
                method TEXT,
                transaction_id TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Discount settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS discount_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                min_quantity INTEGER UNIQUE,
                discount_percent REAL
            )
        ''')
        
        # Referral rewards table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS referral_rewards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER,
                referred_id INTEGER,
                reward_amount REAL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (referrer_id) REFERENCES users (user_id),
                FOREIGN KEY (referred_id) REFERENCES users (user_id)
            )
        ''')
        
        # Referral settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS referral_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_bonus REAL,
                referred_bonus REAL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Initialize default prices if not exists
        default_prices = {
            'hotmail': 10.0,
            'outlook': 10.0,
            'fb_gmail': 10.0
        }
        
        for service, price in default_prices.items():
            cursor.execute(
                "INSERT OR IGNORE INTO prices (service, price) VALUES (?, ?)",
                (service, price)
            )
        
        # Initialize referral settings if not exists
        cursor.execute(
            "INSERT OR IGNORE INTO referral_settings (referrer_bonus, referred_bonus) VALUES (?, ?)",
            (50.0, 25.0)
        )
        
        conn.commit()
        conn.close()
    
    def add_user(self, user_id, username, referral_code=None, referred_by=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Generate referral code if not provided
        if not referral_code:
            referral_code = self.generate_referral_code()
        
        try:
            cursor.execute(
                "INSERT OR IGNORE INTO users (user_id, username, referral_code, referred_by) VALUES (?, ?, ?, ?)",
                (user_id, username, referral_code, referred_by)
            )
            
            # If user was referred, update referrer's count
            if referred_by:
                cursor.execute(
                    "UPDATE users SET total_referrals = total_referrals + 1 WHERE user_id = ?",
                    (referred_by,)
                )
            
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding user: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def generate_referral_code(self, length=8):
        """Generate a random referral code"""
        characters = string.ascii_uppercase + string.digits
        return 'REF' + ''.join(random.choice(characters) for _ in range(length))
    
    def get_user(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
        conn.close()
        return user
    
    def update_balance(self, user_id, amount):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET balance = balance + ? WHERE user_id = ?",
            (amount, user_id)
        )
        conn.commit()
        conn.close()
        return True
    
    def get_balance(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        balance = cursor.fetchone()
        conn.close()
        return balance[0] if balance else 0
    
    def get_price(self, service):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT price FROM prices WHERE service = ?", (service,))
        price = cursor.fetchone()
        conn.close()
        return price[0] if price else 0
    
    def set_price(self, service, price):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE prices SET price = ? WHERE service = ?",
            (price, service)
        )
        conn.commit()
        conn.close()
        return True
    
    def add_deposit_request(self, user_id, amount, method, transaction_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO deposit_requests (user_id, amount, method, transaction_id) VALUES (?, ?, ?, ?)",
            (user_id, amount, method, transaction_id)
        )
        conn.commit()
        conn.close()
        return True
    
    def update_deposit_status(self, user_id, amount, status):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE deposit_requests SET status = ? WHERE user_id = ? AND amount = ? AND status = 'pending'",
            (status, user_id, amount)
        )
        conn.commit()
        conn.close()
        return True
    
    def get_user_id_by_referral_code(self, referral_code):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE referral_code = ?", (referral_code,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

# Additional methods would be implemented here as needed
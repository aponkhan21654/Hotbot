import sqlite3
import logging
from datetime import datetime

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
        from config import DEFAULT_PRICES
        for service, price in DEFAULT_PRICES.items():
            cursor.execute(
                "INSERT OR IGNORE INTO prices (service, price) VALUES (?, ?)",
                (service, price)
            )
        
        # Initialize referral settings if not exists
        from config import REFERRAL_BONUS
        cursor.execute(
            "INSERT OR IGNORE INTO referral_settings (referrer_bonus, referred_bonus) VALUES (?, ?)",
            (REFERRAL_BONUS["referrer"], REFERRAL_BONUS["referred"])
        )
        
        conn.commit()
        conn.close()
    
    def add_user(self, user_id, username, referral_code=None, referred_by=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT OR IGNORE INTO users (user_id, username, referral_code, referred_by) VALUES (?, ?, ?, ?)",
                (user_id, username, referral_code, referred_by)
            )
            
            # If user was referred, update referrer's count and add pending reward
            if referred_by:
                cursor.execute(
                    "UPDATE users SET total_referrals = total_referrals + 1 WHERE user_id = ?",
                    (referred_by,)
                )
                
                # Get referral bonus amount
                cursor.execute("SELECT referred_bonus FROM referral_settings WHERE id = 1")
                referred_bonus = cursor.fetchone()[0]
                
                # Add reward for referred user
                cursor.execute(
                    "UPDATE users SET balance = balance + ? WHERE user_id = ?",
                    (referred_bonus, user_id)
                )
                
                # Add pending reward for referrer
                cursor.execute("SELECT referrer_bonus FROM referral_settings WHERE id = 1")
                referrer_bonus = cursor.fetchone()[0]
                
                cursor.execute(
                    "INSERT INTO referral_rewards (referrer_id, referred_id, reward_amount) VALUES (?, ?, ?)",
                    (referred_by, user_id, referrer_bonus)
                )
            
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding user: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
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
    
    def get_balance(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        balance = cursor.fetchone()
        conn.close()
        return balance[0] if balance else 0
    
    # Additional database methods for prices, deposits, discounts, etc.
    # Would be implemented similarly to the above methods
    
    def __del__(self):
        pass
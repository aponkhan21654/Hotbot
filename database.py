import sqlite3
import os
from typing import List, Tuple, Optional, Dict, Any

def get_db_connection():
    """Create and return a database connection"""
    return sqlite3.connect('bot_data.db', check_same_thread=False)

def init_db():
    """Initialize the database with required tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        balance REAL DEFAULT 0.0,
        referral_code TEXT UNIQUE,
        referred_by INTEGER,
        total_referrals INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (referred_by) REFERENCES users (user_id)
    )
    ''')
    
    # Prices table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS prices (
        service TEXT PRIMARY KEY,
        price REAL DEFAULT 0.0
    )
    ''')
    
    # Insert default prices if not exists
    cursor.execute('INSERT OR IGNORE INTO prices (service, price) VALUES (?, ?)', ('hotmail', 50.0))
    cursor.execute('INSERT OR IGNORE INTO prices (service, price) VALUES (?, ?)', ('outlook', 60.0))
    cursor.execute('INSERT OR IGNORE INTO prices (service, price) VALUES (?, ?)', ('fb_gmail', 70.0))
    
    # Discount settings table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS discount_settings (
        min_quantity INTEGER PRIMARY KEY,
        discount_percent REAL DEFAULT 0.0
    )
    ''')
    
    # Referral settings table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS referral_settings (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        referrer_bonus REAL DEFAULT 50.0,
        referred_bonus REAL DEFAULT 25.0
    )
    ''')
    
    # Insert default referral settings if not exists
    cursor.execute('INSERT OR IGNORE INTO referral_settings (id, referrer_bonus, referred_bonus) VALUES (1, 50.0, 25.0)')
    
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
    
    # Broadcast messages table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS broadcast_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        admin_id INTEGER,
        message_text TEXT,
        sent_count INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    
    conn.commit()
    conn.close()

def db_execute(query: str, params: Tuple = (), fetchone: bool = False, fetchall: bool = False):
    """Execute a database query with parameters"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    
    result = None
    if fetchone:
        result = cursor.fetchone()
    elif fetchall:
        result = cursor.fetchall()
    
    conn.commit()
    conn.close()
    
    return result

def get_user_data(user_id: int):
    """Get user data by user_id"""
    return db_execute(
        'SELECT user_id, username, balance, referral_code, referred_by, total_referrals FROM users WHERE user_id = ?', 
        (user_id,), 
        fetchone=True
    )

def create_user(user_id: int, username: str):
    """Create a new user if not exists"""
    db_execute('INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)', (user_id, username))

def update_user_balance(user_id: int, amount: float):
    """Update user balance"""
    db_execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, user_id))

def get_balance(user_id: int):
    """Get user balance"""
    balance_data = db_execute('SELECT balance FROM users WHERE user_id = ?', (user_id,), fetchone=True)
    return balance_data[0] if balance_data else 0.0

def get_price(service: str):
    """Get price for a service"""
    price_data = db_execute('SELECT price FROM prices WHERE service = ?', (service,), fetchone=True)
    return price_data[0] if price_data else 0.0

def set_price(service: str, price: float):
    """Set price for a service"""
    db_execute('UPDATE prices SET price = ? WHERE service = ?', (price, service))

def get_discount_settings():
    """Get all discount settings"""
    return db_execute('SELECT min_quantity, discount_percent FROM discount_settings ORDER BY min_quantity', fetchall=True)

def update_discount_settings(min_quantity: int, discount_percent: float):
    """Update discount settings"""
    db_execute('INSERT OR REPLACE INTO discount_settings (min_quantity, discount_percent) VALUES (?, ?)', 
               (min_quantity, discount_percent))

def remove_discount_setting(min_quantity: int):
    """Remove a discount setting"""
    db_execute('DELETE FROM discount_settings WHERE min_quantity = ?', (min_quantity,))

def get_referral_settings():
    """Get referral settings"""
    settings = db_execute('SELECT referrer_bonus, referred_bonus FROM referral_settings ORDER BY id DESC LIMIT 1', fetchone=True)
    return settings if settings else (50.0, 25.0)

def update_referral_settings_db(referrer_bonus: float, referred_bonus: float):
    """Update referral settings"""
    db_execute('UPDATE referral_settings SET referrer_bonus = ?, referred_bonus = ? WHERE id = 1', 
               (referrer_bonus, referred_bonus))
    # Insert if not exists
    db_execute('INSERT OR IGNORE INTO referral_settings (id, referrer_bonus, referred_bonus) VALUES (1, ?, ?)', 
               (referrer_bonus, referred_bonus))

def save_deposit_request(user_id: int, amount: float, method: str):
    """Save a deposit request"""
    return db_execute('INSERT INTO deposit_requests (user_id, amount, method) VALUES (?, ?, ?)', 
                     (user_id, amount, method))

def update_deposit_transaction_id(request_id: int, transaction_id: str):
    """Update deposit transaction ID"""
    db_execute('UPDATE deposit_requests SET transaction_id = ? WHERE id = ?', (transaction_id, request_id))

def process_deposit_decision_db(request_id: int, status: str):
    """Process deposit decision (approve/reject)"""
    if status == 'approved':
        request = db_execute('SELECT user_id, amount FROM deposit_requests WHERE id = ?', (request_id,), fetchone=True)
        if request:
            user_id, amount = request
            update_user_balance(user_id, amount)
            db_execute('UPDATE deposit_requests SET status = ? WHERE id = ?', ('approved', request_id))
            return user_id, amount
    elif status == 'rejected':
        db_execute('UPDATE deposit_requests SET status = ? WHERE id = ?', ('rejected', request_id))
    return None, None

def get_pending_deposits():
    """Get all pending deposits"""
    return db_execute('''SELECT dr.id, dr.user_id, u.username, dr.amount, dr.method, dr.transaction_id 
                      FROM deposit_requests dr 
                      JOIN users u ON dr.user_id = u.user_id 
                      WHERE dr.status = 'pending' ''', fetchall=True)

def get_all_user_ids():
    """Get all user IDs"""
    return [row[0] for row in db_execute('SELECT user_id FROM users', fetchall=True)]

def save_broadcast_message_db(admin_id: int, message_text: str):
    """Save broadcast message"""
    return db_execute('INSERT INTO broadcast_messages (admin_id, message_text) VALUES (?, ?)', 
                     (admin_id, message_text))

def update_broadcast_count_db(broadcast_id: int, sent_count: int):
    """Update broadcast count"""
    db_execute('UPDATE broadcast_messages SET sent_count = ? WHERE id = ?', (sent_count, broadcast_id))
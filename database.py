import sqlite3
from datetime import datetime, timedelta

class Database:
    def __init__(self, db_name='bot.db'):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()
    
    def create_tables(self):
        # Таблица пользователей
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                telegram_id INTEGER UNIQUE,
                username TEXT,
                full_name TEXT,
                phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица подписок
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                type TEXT,
                price INTEGER,
                start_date TIMESTAMP,
                end_date TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Таблица заявок
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                order_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                pickup_time TEXT,
                address TEXT,
                comment TEXT,
                status TEXT DEFAULT 'pending',
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        self.conn.commit()
    
    def add_user(self, telegram_id, username, full_name):
        try:
            self.cursor.execute('''
                INSERT OR IGNORE INTO users (telegram_id, username, full_name)
                VALUES (?, ?, ?)
            ''', (telegram_id, username, full_name))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error adding user: {e}")
            return False
    
    def add_subscription(self, user_id, sub_type, price, days):
        start_date = datetime.now()
        end_date = start_date + timedelta(days=days)
        
        self.cursor.execute('''
            INSERT INTO subscriptions (user_id, type, price, start_date, end_date)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, sub_type, price, start_date, end_date))
        self.conn.commit()
    
    def check_subscription(self, user_id):
        self.cursor.execute('''
            SELECT * FROM subscriptions 
            WHERE user_id = ? AND end_date > datetime('now') AND is_active = 1
            ORDER BY end_date DESC LIMIT 1
        ''', (user_id,))
        return self.cursor.fetchone()
    
    def create_order(self, user_id, address, comment, pickup_time):
        self.cursor.execute('''
            INSERT INTO orders (user_id, address, comment, pickup_time)
            VALUES (?, ?, ?, ?)
        ''', (user_id, address, comment, pickup_time))
        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_user_id(self, telegram_id):
        self.cursor.execute('SELECT id FROM users WHERE telegram_id = ?', (telegram_id,))
        result = self.cursor.fetchone()
        return result[0] if result else None

db = Database()
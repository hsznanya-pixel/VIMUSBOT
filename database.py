import sqlite3
from datetime import datetime, timedelta

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('database.db')
        self.create_tables()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Таблица пользователей
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            subscription_end DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Таблица заказов
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            order_time TIMESTAMP,
            pickup_interval TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        
        self.conn.commit()
    
    def add_user(self, user_id, username, full_name):
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, username, full_name) 
        VALUES (?, ?, ?)
        ''', (user_id, username, full_name))
        self.conn.commit()
    
    def update_subscription(self, user_id, days):
        cursor = self.conn.cursor()
        end_date = datetime.now() + timedelta(days=days)
        cursor.execute('''
        UPDATE users SET subscription_end = ? 
        WHERE user_id = ?
        ''', (end_date.strftime('%Y-%m-%d'), user_id))
        self.conn.commit()
    
    def check_subscription(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT subscription_end FROM users WHERE user_id = ?
        ''', (user_id,))
        result = cursor.fetchone()
        
        if result and result[0]:
            end_date = datetime.strptime(result[0], '%Y-%m-%d')
            return end_date > datetime.now()
        return False
    
    def add_order(self, user_id):
        cursor = self.conn.cursor()
        now = datetime.now()
        
        # Определяем интервал вывоза
        if now.hour < 10:
            interval = "10:00 - 14:00"
        else:
            interval = "18:00 - 20:00"
        
        cursor.execute('''
        INSERT INTO orders (user_id, order_time, pickup_interval) 
        VALUES (?, ?, ?)
        ''', (user_id, now.strftime('%Y-%m-%d %H:%M:%S'), interval))
        self.conn.commit()
        return interval
    
    def get_user_orders(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC
        ''', (user_id,))
        return cursor.fetchall()
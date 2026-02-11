import sqlite3
import pandas as pd
from datetime import datetime

DB_NAME = "poker_stats.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = get_connection()
    c = conn.cursor()

    # Таблица Rooms
    c.execute('''CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            deleted_at DATETIME
        )''')

    # Таблица Game Types
    c.execute('''CREATE TABLE IF NOT EXISTS game_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            deleted_at DATETIME
        )''')

    # Таблица Sessions
    c.execute('''CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            room_id INTEGER,
            game_type_id INTEGER,
            buy_in REAL,
            cash_out REAL,
            profit REAL,
            duration_minutes INTEGER,
            comments TEXT,
            FOREIGN KEY (room_id) REFERENCES rooms (id),
            FOREIGN KEY (game_type_id) REFERENCES game_types (id)
        )''')

    # добавить начальные данные

    conn.commit()
    conn.close()


# --- Functions for Rooms ---
def add_room(name):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO rooms (name) VALUES (?)", (name,))
    conn.commit()
    conn.close()

def get_rooms():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM rooms WHERE deleted_at IS NULL ORDER BY id", conn)
    conn.close()
    return df

def soft_delete_room(room_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE rooms SET deleted_at = ? WHERE id = ?", (datetime.now(), room_id))
    conn.commit()
    conn.close()

def update_room(room_id, new_name):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE rooms SET name = ? WHERE id = ?", (new_name, room_id))
    conn.commit()
    conn.close()

# --- Functions for Game Types ---
def add_game_type(name):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO game_types (name) VALUES (?)", (name,))
    conn.commit()
    conn.close()

def get_game_types():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM game_types WHERE deleted_at IS NULL ORDER BY id", conn)
    conn.close()
    return df

def soft_delete_game_type(type_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE game_types SET deleted_at = ? WHERE id = ?", (datetime.now(), type_id))
    conn.commit()
    conn.close()

def update_game_type(type_id, new_name):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE game_types SET name = ? WHERE id = ?", (new_name, type_id))
    conn.commit()
    conn.close()

# --- Functions for Sessions ---
def add_session(date, room_id, game_type_id, buy_in, cash_out, duration, comments = ''):
    profit = cash_out - buy_in
    conn = get_connection()
    c = conn.cursor()
    c.execute('''INSERT INTO sessions 
                 (date, room_id, game_type_id, buy_in, cash_out, profit, duration_minutes, comments) 
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
              (date, room_id, game_type_id, buy_in, cash_out, profit, duration, comments))
    conn.commit()
    conn.close()

def get_sessions_df():
    conn = get_connection()
    query = '''
    SELECT 
        s.id, 
        s.date, 
        COALESCE(r.name, 'Unknown Room') as room, 
        COALESCE(g.name, 'Unknown Game') as game_type, 
        s.buy_in, 
        s.cash_out, 
        s.profit, 
        s.duration_minutes, 
        s.comments,
        s.room_id,
        s.game_type_id
    FROM sessions s
    LEFT JOIN rooms r ON s.room_id = r.id
    LEFT JOIN game_types g ON s.game_type_id = g.id
    ORDER BY s.date DESC, s.id DESC
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()
    df['date'] = pd.to_datetime(df['date'])
    return df

def delete_session(session_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()

def update_session(session_id, date, buy_in, cash_out, duration, comments):
    profit = cash_out - buy_in
    conn = get_connection()
    c = conn.cursor()
    c.execute('''UPDATE sessions 
                 SET date=?, buy_in=?, cash_out=?, profit=?, duration_minutes=?, comments=? 
                 WHERE id=?''',
              (date, buy_in, cash_out, profit, duration, comments, session_id))
    conn.commit()
    conn.close()


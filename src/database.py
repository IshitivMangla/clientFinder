import sqlite3
from datetime import datetime
from . import config

def get_db_connection():
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create leads table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        website TEXT,
        type TEXT,
        address TEXT,
        source TEXT,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Create messages table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lead_id INTEGER,
        message_id TEXT UNIQUE,
        direction TEXT, -- 'outbound' or 'inbound'
        subject TEXT,
        body TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(lead_id) REFERENCES leads(id)
    )
    """)
    
    # Create api_rate_limits table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS api_rate_limits (
        api_name TEXT PRIMARY KEY,
        last_called_at REAL
    )
    """)
    
    # Create api_usage_log table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS api_usage_log (
        api_name TEXT,
        request_date TEXT,
        request_count INTEGER DEFAULT 0,
        PRIMARY KEY (api_name, request_date)
    )
    """)
    
    conn.commit()
    conn.close()

def add_lead(name, email, website, lead_type, address, source, status="pending"):
    if not email:
        return None
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO leads (name, email, website, type, address, source, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(email) DO UPDATE SET
            name=coalesce(excluded.name, name),
            website=coalesce(excluded.website, website),
            type=coalesce(excluded.type, type),
            address=coalesce(excluded.address, address),
            updated_at=CURRENT_TIMESTAMP
        """, (name, email, website, lead_type, address, source, status))
        conn.commit()
        # Get lead ID
        cursor.execute("SELECT id FROM leads WHERE email = ?", (email,))
        row = cursor.fetchone()
        return row[0] if row else None
    except sqlite3.Error as e:
        print(f"Database error adding lead: {e}")
        return None
    finally:
        conn.close()

def get_lead_by_email(email):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM leads WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()
    return row

def update_lead_status(lead_id, status):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE leads SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?
    """, (status, lead_id))
    conn.commit()
    conn.close()

def get_pending_outreach_leads():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM leads 
    WHERE status = 'pending' 
      AND (website IS NULL OR website = '') 
      AND (email IS NOT NULL AND email != '')
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

def log_message(lead_id, message_id, direction, subject, body):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO messages (lead_id, message_id, direction, subject, body)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(message_id) DO NOTHING
        """, (lead_id, message_id, direction, subject, body))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error logging message: {e}")
    finally:
        conn.close()

def get_message_history(lead_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM messages WHERE lead_id = ? ORDER BY timestamp ASC
    """, (lead_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_last_called_time(api_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT last_called_at FROM api_rate_limits WHERE api_name = ?", (api_name,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def set_last_called_time(api_name, timestamp):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO api_rate_limits (api_name, last_called_at)
        VALUES (?, ?)
        ON CONFLICT(api_name) DO UPDATE SET last_called_at = excluded.last_called_at
        """, (api_name, timestamp))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error setting last called time for {api_name}: {e}")
    finally:
        conn.close()

def enforce_rate_limit(api_name, interval_seconds):
    import time
    last_called = get_last_called_time(api_name)
    if last_called:
        elapsed = time.time() - last_called
        if elapsed < interval_seconds:
            wait_time = interval_seconds - elapsed
            print(f"Rate limit for {api_name} hit. Waiting for {wait_time:.2f} seconds...")
            time.sleep(wait_time)
    set_last_called_time(api_name, time.time())

def increment_api_usage(api_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    today = datetime.utcnow().strftime("%Y-%m-%d")
    try:
        cursor.execute("""
        INSERT INTO api_usage_log (api_name, request_date, request_count)
        VALUES (?, ?, 1)
        ON CONFLICT(api_name, request_date) DO UPDATE SET request_count = request_count + 1
        """, (api_name, today))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error incrementing API usage for {api_name}: {e}")
    finally:
        conn.close()

def get_daily_api_count(api_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    today = datetime.utcnow().strftime("%Y-%m-%d")
    cursor.execute("SELECT request_count FROM api_usage_log WHERE api_name = ? AND request_date = ?", (api_name, today))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0

def get_next_unprocessed_lead():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM leads 
    WHERE status IN ('pending', 'discovered') 
    ORDER BY id ASC LIMIT 1
    """)
    row = cursor.fetchone()
    conn.close()
    return row

def update_lead_email(lead_id, email):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE leads SET email = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (email, lead_id))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error updating lead email: {e}")
    finally:
        conn.close()


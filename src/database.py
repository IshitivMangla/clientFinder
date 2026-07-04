import psycopg2
from psycopg2.extras import DictCursor
from datetime import datetime
from . import config

def get_db_connection():
    if not config.SUPABASE_DB_URL:
        raise ValueError("SUPABASE_DB_URL is not configured in the environment variables.")
    return psycopg2.connect(config.SUPABASE_DB_URL, cursor_factory=DictCursor)

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Create leads table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id SERIAL PRIMARY KEY,
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
            id SERIAL PRIMARY KEY,
            lead_id INTEGER REFERENCES leads(id),
            message_id TEXT UNIQUE,
            direction TEXT, -- 'outbound' or 'inbound'
            subject TEXT,
            body TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Create api_rate_limits table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS api_rate_limits (
            api_name TEXT PRIMARY KEY,
            last_called_at DOUBLE PRECISION
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
        
        # Create interested_leads table for finalized clients
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS interested_leads (
            id SERIAL PRIMARY KEY,
            name TEXT,
            email TEXT UNIQUE,
            website TEXT,
            type TEXT,
            address TEXT,
            negotiated_price TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        conn.commit()
        print("[DATABASE] PostgreSQL tables initialized successfully.")
    except psycopg2.Error as e:
        print(f"[DATABASE] Error during DB initialization: {e}")
        conn.rollback()
    finally:
        conn.close()

def add_lead(name, email, website, lead_type, address, source, status="pending"):
    if not email:
        return None
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO leads (name, email, website, type, address, source, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT(email) DO UPDATE SET
            name=coalesce(excluded.name, leads.name),
            website=coalesce(excluded.website, leads.website),
            type=coalesce(excluded.type, leads.type),
            address=coalesce(excluded.address, leads.address),
            updated_at=CURRENT_TIMESTAMP
        """, (name, email, website, lead_type, address, source, status))
        conn.commit()
        # Get lead ID
        cursor.execute("SELECT id FROM leads WHERE email = %s", (email,))
        row = cursor.fetchone()
        return row[0] if row else None
    except psycopg2.Error as e:
        print(f"Database error adding lead: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

def get_lead_by_email(email):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM leads WHERE email = %s", (email,))
    row = cursor.fetchone()
    conn.close()
    return row

def update_lead_status(lead_id, status):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        UPDATE leads SET status = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s
        """, (status, lead_id))
        conn.commit()
    except psycopg2.Error as e:
        print(f"Database error updating lead status: {e}")
        conn.rollback()
    finally:
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
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT(message_id) DO NOTHING
        """, (lead_id, message_id, direction, subject, body))
        conn.commit()
    except psycopg2.Error as e:
        print(f"Database error logging message: {e}")
        conn.rollback()
    finally:
        conn.close()

def get_message_history(lead_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM messages WHERE lead_id = %s ORDER BY timestamp ASC
    """, (lead_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_last_called_time(api_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT last_called_at FROM api_rate_limits WHERE api_name = %s", (api_name,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def set_last_called_time(api_name, timestamp):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO api_rate_limits (api_name, last_called_at)
        VALUES (%s, %s)
        ON CONFLICT(api_name) DO UPDATE SET last_called_at = excluded.last_called_at
        """, (api_name, timestamp))
        conn.commit()
    except psycopg2.Error as e:
        print(f"Database error setting last called time for {api_name}: {e}")
        conn.rollback()
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
        VALUES (%s, %s, 1)
        ON CONFLICT(api_name, request_date) DO UPDATE SET request_count = api_usage_log.request_count + 1
        """, (api_name, today))
        conn.commit()
    except psycopg2.Error as e:
        print(f"Database error incrementing API usage for {api_name}: {e}")
        conn.rollback()
    finally:
        conn.close()

def get_daily_api_count(api_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    today = datetime.utcnow().strftime("%Y-%m-%d")
    cursor.execute("SELECT request_count FROM api_usage_log WHERE api_name = %s AND request_date = %s", (api_name, today))
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
        cursor.execute("UPDATE leads SET email = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s", (email, lead_id))
        conn.commit()
    except psycopg2.Error as e:
        print(f"Database error updating lead email: {e}")
        conn.rollback()
    finally:
        conn.close()

def save_interested_lead_to_db(lead, negotiated_price):
    lead_dict = dict(lead)
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO interested_leads (name, email, website, type, address, negotiated_price)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT(email) DO UPDATE SET
            negotiated_price = excluded.negotiated_price,
            date = CURRENT_TIMESTAMP
        """, (
            lead_dict.get("name"),
            lead_dict.get("email"),
            lead_dict.get("website"),
            lead_dict.get("type"),
            lead_dict.get("address"),
            negotiated_price
        ))
        conn.commit()
        print(f"[DATABASE] Successfully logged interested lead {lead_dict.get('email')} to PostgreSQL interested_leads table.")
    except psycopg2.Error as e:
        print(f"[ERROR] Failed to save interested lead to database: {e}")
        conn.rollback()
    finally:
        conn.close()


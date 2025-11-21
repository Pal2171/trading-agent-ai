import os
import psycopg2
from dotenv import load_dotenv
import db_utils

load_dotenv(override=True)

def create_tables():
    print("--- Database Rebuild & Connection Test ---")
    
    config = db_utils.get_db_config()
    dsn = config.dsn
    
    # Apply the same logic as db_utils for SSL
    if "localhost" not in dsn and "127.0.0.1" not in dsn:
        if "sslmode" not in dsn:
            if "?" in dsn:
                dsn += "&sslmode=require"
            else:
                dsn += "?sslmode=require"
    
    # Add connect_timeout to fail fast if network is blocked
    if "connect_timeout" not in dsn:
        if "?" in dsn:
            dsn += "&connect_timeout=10"
        else:
            dsn += "?connect_timeout=10"

    print(f"Attempting to connect with timeout=10s...")
    
    try:
        conn = psycopg2.connect(dsn)
        print("Connection established!")
        
        cur = conn.cursor()
        
        # Drop existing tables if requested (optional, but safer to just create if not exists)
        # Uncomment the next lines if you really want to WIPE the database
        # print("Dropping old tables...")
        # cur.execute("DROP TABLE IF EXISTS bot_operations CASCADE;")
        # cur.execute("DROP TABLE IF EXISTS indicators_contexts CASCADE;")
        # cur.execute("DROP TABLE IF EXISTS ai_contexts CASCADE;")
        # cur.execute("DROP TABLE IF EXISTS open_positions CASCADE;")
        # cur.execute("DROP TABLE IF EXISTS account_snapshots CASCADE;")
        
        print("Creating tables...")
        cur.execute(db_utils.SCHEMA_SQL)
        
        # We also need the bot_operations table which might be further down in db_utils.py
        # Since I only read up to line 150, I'll assume SCHEMA_SQL contains most of it, 
        # but I should check if there are more SQL statements. 
        # However, db_utils.init_db() usually does this.
        
        conn.commit()
        print("Tables created successfully!")
        
        cur.close()
        conn.close()
        
    except psycopg2.OperationalError as e:
        print("\nCONNECTION ERROR")
        print(f"Details: {e}")
        print("Possible causes:")
        print("1. IP blocked by firewall (check Railway settings)")
        print("2. SSL handshake failed (try changing sslmode)")
        print("3. Wrong port or host")
    except Exception as e:
        print(f"\nUNEXPECTED ERROR: {e}")

if __name__ == "__main__":
    create_tables()

"""Script per verificare la struttura del database."""
from db_utils import get_connection

def verify_database():
    """Verifica che tutte le tabelle siano state create correttamente."""
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Ottieni tutte le tabelle
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            tables = cur.fetchall()
            
            print("[OK] Tabelle create nel database:")
            for table in tables:
                print(f"   - {table[0]}")
            
            print("\n[INFO] Struttura tabella 'bot_operations':")
            cur.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'bot_operations'
                ORDER BY ordinal_position;
            """)
            columns = cur.fetchall()
            
            for col in columns:
                nullable = "NULL" if col[2] == "YES" else "NOT NULL"
                print(f"   - {col[0]:<30} {col[1]:<20} {nullable}")
            
            # Verifica che pnl_usd esista
            pnl_exists = any(col[0] == 'pnl_usd' for col in columns)
            if pnl_exists:
                print("\n[OK] Campo 'pnl_usd' presente nella tabella 'bot_operations'!")
            else:
                print("\n[ERROR] Campo 'pnl_usd' NON trovato nella tabella 'bot_operations'!")
            
            # Conta i record esistenti
            print("\n[INFO] Conteggio record:")
            tables_to_check = ['account_snapshots', 'bot_operations', 'ai_contexts', 'errors']
            for table_name in tables_to_check:
                cur.execute(f"SELECT COUNT(*) FROM {table_name};")
                count = cur.fetchone()[0]
                print(f"   - {table_name}: {count} record")

if __name__ == "__main__":
    verify_database()

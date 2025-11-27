#!/usr/bin/env python3
"""Script per pulire il database dalle vecchie operazioni e ripartire puliti"""

import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

def clean_database():
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        raise RuntimeError("DATABASE_URL non impostata")
    
    print("=" * 60)
    print("🧹 PULIZIA DATABASE - Capital.com Fresh Start")
    print("=" * 60)
    
    conn = psycopg2.connect(dsn)
    cur = conn.cursor()
    
    try:
        # 1. Conta i record esistenti
        tables = [
            'account_snapshots',
            'open_positions', 
            'ai_contexts',
            'indicators_contexts',
            'news_contexts',
            'sentiment_contexts',
            'forecasts_contexts',
            'bot_operations',
            'real_positions',
            'trades_history',
            'errors'
        ]
        
        print("\n📊 Record esistenti prima della pulizia:")
        for table in tables:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                count = cur.fetchone()[0]
                print(f"   {table}: {count}")
            except Exception as e:
                print(f"   {table}: (tabella non esiste)")
        
        # 2. Chiedi conferma
        print("\n⚠️  Questa operazione cancellerà TUTTI i dati storici!")
        print("   Verranno mantenute solo le strutture delle tabelle.\n")
        
        confirm = input("Vuoi procedere con la pulizia? (y/N): ").strip().lower()
        if confirm != 'y':
            print("\n❌ Operazione annullata")
            return
        
        # 3. Pulisci le tabelle (in ordine inverso per le FK)
        print("\n🗑️  Pulizia in corso...")
        
        # Ordine di cancellazione (rispetta le FK)
        delete_order = [
            'trades_history',
            'real_positions',
            'errors',
            'bot_operations',
            'forecasts_contexts',
            'sentiment_contexts',
            'news_contexts',
            'indicators_contexts',
            'ai_contexts',
            'open_positions',
            'account_snapshots'
        ]
        
        for table in delete_order:
            try:
                cur.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE")
                print(f"   ✅ {table} pulita")
            except Exception as e:
                print(f"   ⚠️ {table}: {e}")
        
        conn.commit()
        
        # 4. Verifica
        print("\n📊 Record dopo la pulizia:")
        for table in tables:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                count = cur.fetchone()[0]
                print(f"   {table}: {count}")
            except:
                pass
        
        print("\n" + "=" * 60)
        print("✅ DATABASE PULITO - Pronto per Capital.com!")
        print("=" * 60)
        
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    clean_database()

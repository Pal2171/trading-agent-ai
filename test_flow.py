"""Test completo del flusso Capital.com + DB"""
import os
import json
from dotenv import load_dotenv

load_dotenv()

print("="*60)
print("TEST FLUSSO COMPLETO CAPITAL.COM + DB")
print("="*60)

# 1. Test Capital.com connection
print("\n1️⃣ Test connessione Capital.com...")
from capital_trader import CapitalTrader
bot = CapitalTrader(
    api_key=os.getenv('CAPITAL_API_KEY'),
    password=os.getenv('CAPITAL_API_PASSWORD'),
    identifier=os.getenv('CAPITAL_IDENTIFIER'),
    demo_mode=True
)

# 2. Get account status
print("\n2️⃣ Account Status...")
status = bot.get_account_status_formatted()
print(f"   Account: {status.get('account_name')}")
print(f"   Balance: €{status.get('balance_usd'):,.2f}")
print(f"   Posizioni: {len(status.get('positions', []))}")

for pos in status.get('positions', []):
    print(f"      - {pos['symbol']}: {pos['side']} {pos['size']} @ {pos.get('entry_price')}")
    print(f"        deal_id: {pos.get('deal_id')}")

# 3. Test sync_real_positions
print("\n3️⃣ Test sync posizioni nel DB...")
import db_utils
positions = status.get('positions', [])
synced = db_utils.sync_real_positions(positions)
print(f"   Sincronizzate: {synced} posizioni")

# 4. Verifica nel DB
print("\n4️⃣ Verifica dati nel DB...")
import psycopg2
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

cur.execute("SELECT deal_id, symbol, direction, size, entry_price, pnl_usd FROM real_positions")
rows = cur.fetchall()
print(f"   Posizioni in real_positions: {len(rows)}")
for row in rows:
    print(f"      - {row[0]}: {row[1]} {row[2]} {row[3]} @ {row[4]} (PnL: {row[5]})")

cur.close()
conn.close()

# 5. Test log_account_status
print("\n5️⃣ Test log_account_status...")
snapshot_id = db_utils.log_account_status(status)
print(f"   Snapshot salvato con id={snapshot_id}")

print("\n" + "="*60)
print("✅ TEST COMPLETATO")
print("="*60)

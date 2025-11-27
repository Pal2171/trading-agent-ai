"""Test selezione conto Capital.com"""
from capital_trader import CapitalTrader
import os
from dotenv import load_dotenv

load_dotenv()

print("="*50)
print("TEST SELEZIONE CONTO CAPITAL.COM")
print("="*50)

bot = CapitalTrader(
    api_key=os.getenv('CAPITAL_API_KEY'),
    password=os.getenv('CAPITAL_API_PASSWORD'),
    identifier=os.getenv('CAPITAL_IDENTIFIER'),
    demo_mode=True
)

status = bot.get_account_status()
print(f"\n📊 Conto attivo: {status.get('account_name')}")
print(f"💰 Balance: €{status.get('balance'):,.2f}")
print(f"📈 Equity: €{status.get('equity', status.get('balance')):,.2f}")
print(f"💵 Available: €{status.get('available'):,.2f}")
print(f"📉 P&L: €{status.get('pnl'):,.2f}")

# Verifica posizioni
positions = bot.get_open_positions()
print(f"\n🎯 Posizioni aperte: {len(positions)}")
for pos in positions:
    print(f"   - {pos.get('epic', 'N/A')}: {pos.get('direction')} {pos.get('size')}")

print("\n" + "="*50)

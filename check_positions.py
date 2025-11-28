from capital_trader import CapitalTrader
import os
from dotenv import load_dotenv
load_dotenv()

# Account 1: Conto solo Crypto
print('='*60)
print('CONTO SOLO CRYPTO (trading-agent-ai)')
print('='*60)
bot1 = CapitalTrader(
    api_key=os.getenv('CAPITAL_API_KEY'),
    password=os.getenv('CAPITAL_API_PASSWORD'),
    identifier=os.getenv('CAPITAL_IDENTIFIER'),
    demo_mode=True,
    account_id='299530594022675614'
)
positions1 = bot1.get_open_positions()
if positions1:
    for p in positions1:
        symbol = p.get('symbol', 'N/A')
        direction = p.get('direction', 'N/A')
        size = p.get('size', 'N/A')
        entry = p.get('entry_price', 'N/A')
        pnl = p.get('pnl', 'N/A')
        print(f"  {symbol} {direction} | Size: {size} | Entry: {entry} | PnL: {pnl}")
else:
    print('  Nessuna posizione aperta')

print()
print('='*60)
print('CONTO TS PAOLO (Trading-Agent-Capital)')
print('='*60)
bot2 = CapitalTrader(
    api_key=os.getenv('CAPITAL_API_KEY'),
    password=os.getenv('CAPITAL_API_PASSWORD'),
    identifier=os.getenv('CAPITAL_IDENTIFIER'),
    demo_mode=True,
    account_id='299043377227584670'
)
positions2 = bot2.get_open_positions()
if positions2:
    for p in positions2:
        symbol = p.get('symbol', 'N/A')
        direction = p.get('direction', 'N/A')
        size = p.get('size', 'N/A')
        entry = p.get('entry_price', 'N/A')
        pnl = p.get('pnl', 'N/A')
        print(f"  {symbol} {direction} | Size: {size} | Entry: {entry} | PnL: {pnl}")
else:
    print('  Nessuna posizione aperta')

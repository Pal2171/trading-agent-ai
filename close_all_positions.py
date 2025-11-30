"""Script per chiudere tutte le posizioni aperte"""
import os
from dotenv import load_dotenv
from capital_trader import CapitalTrader

load_dotenv()

print("="*60)
print("CHIUSURA TUTTE LE POSIZIONI")
print("="*60)

# Connessione al conto Crypto
bot = CapitalTrader(
    api_key=os.getenv('CAPITAL_API_KEY'),
    password=os.getenv('CAPITAL_API_PASSWORD'),
    identifier=os.getenv('CAPITAL_IDENTIFIER'),
    demo_mode=True,
    account_id='299530594022675614'  # Conto solo Crypto
)

positions = bot.get_open_positions()

if not positions:
    print("\n✅ Nessuna posizione aperta!")
else:
    print(f"\n📊 Trovate {len(positions)} posizioni da chiudere:")
    
    for p in positions:
        symbol = p.get('symbol', 'N/A')
        direction = p.get('direction', 'N/A')
        pnl = p.get('pnl', 0)
        deal_id = p.get('dealId')
        
        print(f"\n⚡ Chiusura {symbol} {direction} (PnL: {pnl})...")
        result = bot.close_position(deal_id)
        
        if result.get('status') == 'ok':
            print(f"   ✅ Chiusa con successo!")
        else:
            print(f"   ❌ Errore: {result}")

# Verifica finale
print("\n" + "="*60)
print("VERIFICA FINALE")
print("="*60)
positions_after = bot.get_open_positions()
if positions_after:
    print("⚠️ Posizioni ancora aperte:")
    for p in positions_after:
        print(f"  {p.get('symbol')} {p.get('direction')} | PnL: {p.get('pnl')}")
else:
    print("✅ Tutte le posizioni sono state chiuse!")

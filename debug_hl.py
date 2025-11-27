"""Script di debug per verificare lo stato di Hyperliquid"""
import os
import json
from dotenv import load_dotenv
from hyperliquid_trader import HyperLiquidTrader

load_dotenv()

PRIVATE_KEY = os.getenv("PRIVATE_KEY")
WALLET_ADDRESS = os.getenv("WALLET_ADDRESS")

print("="*60)
print("DEBUG HYPERLIQUID CONNECTION")
print("="*60)

bot = HyperLiquidTrader(
    secret_key=PRIVATE_KEY,
    account_address=WALLET_ADDRESS,
    testnet=True
)

# 1. Stato account
print("\n📊 STATO ACCOUNT:")
print("-"*40)
status = bot.get_account_status()
print(f"Balance USD: ${status['balance_usd']:.2f}")

print("\n🎯 POSIZIONI APERTE:")
print("-"*40)
if status['open_positions']:
    for pos in status['open_positions']:
        print(f"  {pos['symbol']}: {pos['side'].upper()} {pos['size']} @ ${pos['entry_price']:.2f}")
        print(f"    Mark: ${pos['mark_price']:.2f} | PnL: ${pos['pnl_usd']:.2f} | Leva: {pos['leverage']}")
else:
    print("  Nessuna posizione aperta")

# 2. Limiti per BTC
print("\n📋 LIMITI TRADING BTC:")
print("-"*40)
bot.debug_symbol_limits("BTC")

# 3. Test chiusura manuale con log dettagliato
print("\n🔧 TEST CLOSE (senza eseguire):")
print("-"*40)

# Ottieni info user_state raw
user_state = bot.info.user_state(WALLET_ADDRESS)
print("\nRaw assetPositions:")
for pos in user_state.get('assetPositions', []):
    print(f"  {json.dumps(pos, indent=2)}")

# Verifica se c'è una posizione BTC
btc_positions = [p for p in user_state.get('assetPositions', []) 
                 if p.get('position', {}).get('coin') == 'BTC']

if btc_positions:
    print(f"\n✅ Trovata posizione BTC da chiudere")
    btc_pos = btc_positions[0]['position']
    size = float(btc_pos.get('szi', 0))
    print(f"   Size: {size}")
    print(f"   Entry: {btc_pos.get('entryPx')}")
    
    # Verifica prezzo oracle
    all_mids = bot.info.all_mids()
    btc_mid = all_mids.get('BTC', 'N/A')
    print(f"   Mid price: {btc_mid}")
    
    # Test chiusura
    print("\n⚡ Tentativo di chiusura BTC...")
    try:
        result = bot.exchange.market_close("BTC")
        print(f"   Risultato: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"   ❌ Errore: {e}")
else:
    print("\n⚠️ Nessuna posizione BTC trovata - non c'è nulla da chiudere!")

print("\n" + "="*60)

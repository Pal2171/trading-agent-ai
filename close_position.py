"""Script per chiudere manualmente posizione su Hyperliquid Testnet"""
import os
from dotenv import load_dotenv
from hyperliquid_trader import HyperLiquidTrader

load_dotenv()

PRIVATE_KEY = os.getenv("PRIVATE_KEY")
WALLET_ADDRESS = os.getenv("WALLET_ADDRESS")

print("="*60)
print("CHIUSURA MANUALE POSIZIONE HYPERLIQUID TESTNET")
print("="*60)

bot = HyperLiquidTrader(
    secret_key=PRIVATE_KEY,
    account_address=WALLET_ADDRESS,
    testnet=True
)

# Verifica posizioni aperte
status = bot.get_account_status()
print(f"\n💰 Balance: ${status['balance_usd']:.2f}")

if not status['open_positions']:
    print("\n✅ Nessuna posizione aperta!")
    exit()

print("\n📊 Posizioni aperte:")
for i, pos in enumerate(status['open_positions']):
    print(f"  [{i+1}] {pos['symbol']}: {pos['side'].upper()} {pos['size']} @ ${pos['entry_price']:.2f}")
    print(f"      PnL: ${pos['pnl_usd']:.2f}")

# Chiedi conferma
symbol = input("\n❓ Quale posizione vuoi chiudere? (es: BTC, oppure 'q' per uscire): ").strip().upper()

if symbol == 'Q':
    print("Uscita.")
    exit()

# Verifica che la posizione esista
pos_to_close = None
for pos in status['open_positions']:
    if pos['symbol'] == symbol:
        pos_to_close = pos
        break

if not pos_to_close:
    print(f"❌ Nessuna posizione trovata per {symbol}")
    exit()

print(f"\n⚡ Tentativo chiusura {symbol} {pos_to_close['side'].upper()}...")
print("-"*40)

try:
    result = bot.exchange.market_close(symbol)
    print(f"\n📤 Risultato: {result}")
    
    if result.get('status') == 'ok':
        print("\n✅ Posizione chiusa con successo!")
    else:
        print("\n⚠️ La chiusura potrebbe essere fallita.")
        print("Prova a chiudere manualmente su: https://app.hyperliquid-testnet.xyz/")
        
except Exception as e:
    print(f"\n❌ Errore: {e}")
    print("\nProva a chiudere manualmente su: https://app.hyperliquid-testnet.xyz/")

print("\n" + "="*60)

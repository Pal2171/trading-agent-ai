
import sys
sys.stdout.reconfigure(encoding='utf-8')
import patch_ssl

from indicators import analyze_multiple_tickers
from news_feed import fetch_latest_news
from trading_agent import previsione_trading_agent
from whalealert import format_whale_alerts_to_string
from sentiment import get_sentiment
from forecaster import get_crypto_forecasts
from hyperliquid_trader import HyperLiquidTrader
import os
import json
import db_utils
from dotenv import load_dotenv
load_dotenv()

# Collegamento ad Hyperliquid
TESTNET = True   # True = testnet, False = mainnet (occhio!)
VERBOSE = True    # stampa informazioni extra
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
WALLET_ADDRESS = os.getenv("WALLET_ADDRESS")

if not PRIVATE_KEY or not WALLET_ADDRESS:
    raise RuntimeError("PRIVATE_KEY o WALLET_ADDRESS mancanti nel .env")

print("=" * 60)
print("🤖 TRADING BOT STARTED")
print("=" * 60)

try:
    print("\n1️⃣ Connecting to HyperLiquid...")
    bot = HyperLiquidTrader(
        secret_key=PRIVATE_KEY,
        account_address=WALLET_ADDRESS,
        testnet=TESTNET
    )
    print("   ✅ HyperLiquid connected")

    # Calcolo delle informazioni in input per Ticker
    tickers = ['BTC', 'ETH', 'SOL']
    print(f"\n2️⃣ Analyzing indicators for {tickers}...")
    indicators_txt, indicators_json  = analyze_multiple_tickers(tickers)
    print("   ✅ Indicators analyzed")
    
    print("\n3️⃣ Fetching latest news...")
    news_txt = fetch_latest_news()
    print("   ✅ News fetched")
    
    # whale_alerts_txt = format_whale_alerts_to_string()
    
    print("\n4️⃣ Analyzing sentiment...")
    sentiment_txt, sentiment_json  = get_sentiment()
    print("   ✅ Sentiment analyzed")
    
    print("\n5️⃣ Getting price forecasts...")
    forecasts_txt, forecasts_json = get_crypto_forecasts()
    print("   ✅ Forecasts retrieved")


    print("\n6️⃣ Preparing data for AI analysis...")
    msg_info=f"""<indicatori>\n{indicators_txt}\n</indicatori>\n\n
    <news>\n{news_txt}</news>\n\n
    <sentiment>\n{sentiment_txt}\n</sentiment>\n\n
    <forecast>\n{forecasts_txt}\n</forecast>\n\n"""

    print("\n7️⃣ Getting account status from HyperLiquid...")
    account_status = bot.get_account_status()
    portfolio_data = f"{json.dumps(account_status)}"
    print("   ✅ Account status retrieved")
    print("\n8️⃣ Logging account snapshot to database...")
    snapshot_id = db_utils.log_account_status(account_status)
    print(f"   ✅ Snapshot saved (id={snapshot_id})")


    # Creating System prompt with recent operations context
    print("\n9️⃣ Loading optimized system prompt...")
    with open('system_prompt_optimized.txt', 'r', encoding='utf-8') as f:
        system_prompt = f.read()
    
    # Get recent operations for context (last 5)
    print("   📊 Fetching recent operations...")
    recent_ops = db_utils.get_recent_bot_operations(limit=5)
    
    # Format recent operations context
    if recent_ops:
        ops_context = "**LAST 5 OPERATIONS:\n"
        for i, op in enumerate(recent_ops, 1):
            created_at = op.get('created_at', 'N/A')
            operation = op.get('operation', 'N/A')
            symbol = op.get('symbol', 'N/A')
            direction = op.get('direction', 'N/A')
            reason_short = op.get('reason', 'N/A')
            if len(reason_short) > 80:
                reason_short = reason_short[:77] + '...'
            ops_context += f"{i}. {created_at} | {operation.upper()} {symbol} {direction.upper()} - {reason_short}\n"
        
        ops_context += "\n**ANTI-OVERTRADING CHECK:**\n"
        ops_context += f"- Total recent ops: {len(recent_ops)}\n"
        recent_closes = [op for op in recent_ops if op.get('operation', '').lower() == 'close']
        if recent_closes:
            ops_context += f"- Recent CLOSE operations: {len(recent_closes)}\n"
            ops_context += "- ⚠️ Be CONSERVATIVE if re-entering same coin\n"
        symbols_count = {}
        for op in recent_ops[:3]:
            sym = op.get('symbol', '')
            if sym:
                symbols_count[sym] = symbols_count.get(sym, 0) + 1
        repeated_symbols = [sym for sym, count in symbols_count.items() if count >= 2]
        if repeated_symbols:
            ops_context += f"- ⚠️ REPEATED on {', '.join(repeated_symbols)} - Consider SKIP for 1h\n"
    else:
        ops_context = "**FIRST OPERATION** - No historical context available.\n"
    
    # Replace placeholders using .replace() instead of .format() to avoid JSON {} conflicts
    system_prompt = system_prompt.replace('{RECENT_OPS}', ops_context)
    system_prompt = system_prompt.replace('{PORTFOLIO}', portfolio_data)
    system_prompt = system_prompt.replace('{MARKET_DATA}', msg_info)
    print("   ✅ System prompt ready (optimized + recent ops context)")

        
    print("\n🧠 Calling AI Agent for trading decision...")
    out = previsione_trading_agent(system_prompt)
    print(f"   ✅ AI Decision: {out.get('action', 'UNKNOWN')}")
    
    print("\n📊 Executing trading signal...")
    bot.execute_signal(out)
    print("   ✅ Signal executed")

    # ------------------------------------------------------
    # GESTIONE STOP LOSS / TRAILING STOP INTELLIGENTE
    # ------------------------------------------------------
    print("\n🛡️ Checking stop loss and position management...")
    try:
        # Rileggiamo lo stato aggiornato dopo l'esecuzione
        updated_status = bot.get_account_status()
        print(f"   📈 Open positions: {len(updated_status['open_positions'])}")
        
        for pos in updated_status['open_positions']:
            symbol = pos['symbol']
            side = pos['side'] # "long" o "short"
            size = float(pos['size'])
            entry_price = float(pos['entry_price'])
            pnl_pct = (pos['pnl_usd'] / (entry_price * size)) * 100 if size > 0 else 0
            
            # Cerchiamo i dati dell'indicatore per questo simbolo
            indicator_data = next((d for d in indicators_json if d['ticker'] == symbol), None)
            
            if indicator_data:
                curr_price = indicator_data['current']['price']
                supertrend = indicator_data['current']['supertrend']
                atr_14 = indicator_data['longer_term_15m'].get('atr_14_current', 0)
                
                # ========== STRATEGIA STOP LOSS DINAMICA ==========
                
                sl_price = 0.0
                stop_strategy = ""
                
                # 1. Calcola trailing stop percentuale base
                if pnl_pct > 6:
                    # Profitto > 6%: trailing stop a 3% dal picco
                    trailing_pct = 0.03
                    stop_strategy = "Trailing Stop (Profit > 6%)"
                elif pnl_pct > 4:
                    # Profitto 4-6%: lock 2% profit
                    trailing_pct = (pnl_pct - 2) * 0.01
                    stop_strategy = "Profit Lock (2%)"
                elif pnl_pct > 2:
                    # Profitto 2-4%: break-even
                    trailing_pct = pnl_pct * 0.01
                    stop_strategy = "Break-Even Protection"
                else:
                    # Nessun profitto significativo: stop loss base più largo
                    trailing_pct = 0.035  # 3.5% stop loss iniziale (più spazio per respirare)
                    stop_strategy = "Initial Stop Loss"
                
                # 2. Usa ATR per stop loss volatility-adjusted
                # Dai più spazio su asset volatili, ma non troppo stretto su quelli stabili
                if atr_14 > 0:
                    atr_multiplier = 2.5  # 2.5x ATR (era 2.0x - ora più permissivo)
                    atr_stop_distance = (atr_14 * atr_multiplier) / curr_price
                    
                    # Usa il più ampio tra % fisso e ATR-based, ma con limiti ragionevoli
                    if atr_stop_distance > trailing_pct:
                        # Non superare il 6% anche su asset molto volatili
                        trailing_pct = min(atr_stop_distance, 0.06)
                        stop_strategy += " (ATR-adjusted)"
                
                # 3. Calcola prezzo stop loss
                if side == "long":
                    sl_price = curr_price * (1 - trailing_pct)
                    is_buy_sl = False  # Chiudere Long = Sell
                    
                    # SUPERTREND CHECK: Se Supertrend diventa BEARISH, chiudi immediatamente
                    if supertrend == "BEARISH":
                        print(f"🚨 SUPERTREND FLIP DETECTED for {symbol}! Closing LONG position immediately.")
                        bot.exchange.market_close(symbol)
                        continue  # Skip stop loss placement
                        
                else:  # short
                    sl_price = curr_price * (1 + trailing_pct)
                    is_buy_sl = True  # Chiudere Short = Buy
                    
                    # SUPERTREND CHECK: Se Supertrend diventa BULLISH, chiudi immediatamente
                    if supertrend == "BULLISH":
                        print(f"🚨 SUPERTREND FLIP DETECTED for {symbol}! Closing SHORT position immediately.")
                        bot.exchange.market_close(symbol)
                        continue  # Skip stop loss placement
                
                print(f"\n📊 Stop Loss Update for {symbol}:")
                print(f"   Side: {side.upper()}")
                print(f"   Entry: ${entry_price:.2f}, Current: ${curr_price:.2f}")
                print(f"   P&L: {pnl_pct:.2f}%")
                print(f"   Strategy: {stop_strategy}")
                print(f"   Stop Price: ${sl_price:.2f} ({trailing_pct*100:.2f}% from current)")
                
                # Cancelliamo vecchi ordini (Trailing: sposta lo stop)
                bot.cancel_all_orders(symbol)
                
                # Piazziamo nuovo SL
                bot.place_stop_loss(symbol, is_buy_sl, sl_price, size)
                
    except Exception as e:
        print(f"⚠️ Errore gestione Stop Loss: {e}")
        import traceback
        traceback.print_exc()


    print("\n💾 Logging operation to database...")
    op_id = db_utils.log_bot_operation(out, system_prompt=system_prompt, indicators=indicators_json, news_text=news_txt, sentiment=sentiment_json, forecasts=forecasts_json)
    print(f"   ✅ Operation logged (id={op_id})")
    
    print("\n" + "=" * 60)
    print("✅ TRADING BOT COMPLETED SUCCESSFULLY")
    print("=" * 60)

except Exception as e:
    print("\n" + "=" * 60)
    print("❌ ERROR OCCURRED")
    print("=" * 60)
    print(f"Error: {str(e)}")
    import traceback
    print(traceback.format_exc())
    
    # Se system_prompt non è definito (errore prima), usiamo stringa vuota
    if 'system_prompt' not in locals():
        system_prompt = "N/A"
    if 'indicators_json' not in locals():
        indicators_json = {}
    if 'news_txt' not in locals():
        news_txt = "N/A"
    if 'sentiment_json' not in locals():
        sentiment_json = {}
    if 'forecasts_json' not in locals():
        forecasts_json = {}
    if 'account_status' not in locals():
        account_status = {}

    # Temporarily commented out - errors table doesn't exist yet
    # db_utils.log_error(e, context={"prompt": system_prompt, "tickers": tickers,
    #                                 "indicators":indicators_json, "news":news_txt,
    #                                 }, source="trading_agent")
    print(f"An error occurred: {e}")
    import traceback
    traceback.print_exc()

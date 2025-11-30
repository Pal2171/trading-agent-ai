import sys
sys.stdout.reconfigure(encoding='utf-8')

from indicators import analyze_multiple_tickers
from news_feed import fetch_latest_news
from trading_agent import previsione_trading_agent
from sentiment import get_sentiment
from forecaster import get_crypto_forecasts
from capital_trader import CapitalTrader
import os
import json
import db_utils
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
load_dotenv()

# --- ANTI-OVERTRADING CONFIGURATION ---
# Tempo minimo prima di poter chiudere una posizione (in minuti)
MIN_POSITION_HOLD_MINUTES = 60  # Mantieni posizione almeno 1 ora
# Perdita minima (%) per permettere chiusura anticipata (stop loss)
STOP_LOSS_THRESHOLD_PCT = -3.0  # Chiudi se perdita > 3%
# Profitto minimo (%) per permettere take profit anticipato
TAKE_PROFIT_THRESHOLD_PCT = 2.0  # Chiudi se profitto > 2%

# --- CONFIGURATION ---
# Capital.com credentials
CAPITAL_API_KEY = os.getenv("CAPITAL_API_KEY")
CAPITAL_PASSWORD = os.getenv("CAPITAL_API_PASSWORD")
CAPITAL_IDENTIFIER = os.getenv("CAPITAL_IDENTIFIER")
CAPITAL_DEMO = os.getenv("CAPITAL_DEMO_MODE", "True").lower() == "true"
CAPITAL_ACCOUNT_ID = os.getenv("CAPITAL_ACCOUNT_ID")  # Account specifico (opzionale)

# Tickers - Capital.com EPICs per crypto
TICKERS = ['BTC', 'ETH', 'SOL']  # Verranno mappati a BTCUSD, ETHUSD, SOLUSD

# Inizializza variabili per error handling
system_prompt = None
indicators_json = None
news_txt = None
sentiment_json = None
forecasts_json = None
account_status = None

# Verifica credenziali
if not CAPITAL_API_KEY or not CAPITAL_PASSWORD or not CAPITAL_IDENTIFIER:
    raise RuntimeError("Credenziali Capital.com mancanti nel .env (CAPITAL_API_KEY, CAPITAL_API_PASSWORD, CAPITAL_IDENTIFIER)")

try:
    print("="*60)
    print(f"🤖 TRADING BOT - Capital.com {'DEMO' if CAPITAL_DEMO else 'LIVE'}")
    print("="*60)
    
    # 1. Connessione a Capital.com
    print("\n1️⃣ Connessione a Capital.com...")
    bot = CapitalTrader(
        api_key=CAPITAL_API_KEY,
        password=CAPITAL_PASSWORD,
        identifier=CAPITAL_IDENTIFIER,
        demo_mode=CAPITAL_DEMO,
        account_id=CAPITAL_ACCOUNT_ID  # Forza account specifico da env
    )
    print("   ✅ Connesso a Capital.com")

    # 2. Analisi indicatori tecnici
    print(f"\n2️⃣ Analisi indicatori per {TICKERS}...")
    indicators_txt, indicators_json = analyze_multiple_tickers(TICKERS, capital_client=bot)
    print("   ✅ Indicatori calcolati")

    # 3. News
    print("\n3️⃣ Recupero news crypto...")
    news_txt = fetch_latest_news()
    print("   ✅ News recuperate")

    # 4. Sentiment
    print("\n4️⃣ Analisi sentiment...")
    sentiment_txt, sentiment_json = get_sentiment()
    print("   ✅ Sentiment analizzato")

    # 5. Forecasts
    print("\n5️⃣ Generazione previsioni Prophet...")
    forecasts_txt, forecasts_json = get_crypto_forecasts(tickers=TICKERS, capital_client=bot)
    print("   ✅ Previsioni generate")

    # 6. Costruzione messaggio per AI
    msg_info = f"""<indicatori>
{indicators_txt}
</indicatori>

<news>
{news_txt}
</news>

<sentiment>
{sentiment_txt}
</sentiment>

<forecast>
{forecasts_txt}
</forecast>
"""

    # 7. Stato account
    print("\n6️⃣ Recupero stato account...")
    account_status = bot.get_account_status_formatted()
    portfolio_data = json.dumps(account_status)
    snapshot_id = db_utils.log_account_status(account_status)
    print(f"   ✅ Snapshot salvato con id={snapshot_id}")
    
    # Sincronizza posizioni reali nel DB per la dashboard
    positions = account_status.get('positions', [])
    synced_count = db_utils.sync_real_positions(positions)
    print(f"   ✅ Sincronizzate {synced_count} posizioni reali")

    # 8. Creazione System Prompt
    print("\n7️⃣ Preparazione prompt per AI...")
    with open('system_prompt.txt', 'r') as f:
        system_prompt = f.read()
    system_prompt = system_prompt.format(portfolio_data, msg_info)
    print("   ✅ Prompt preparato")

    # 9. Chiamata AI
    print("\n8️⃣ L'agente AI sta decidendo...")
    out = previsione_trading_agent(system_prompt)
    
    # 9.5 ANTI-OVERTRADING: Verifica se l'AI vuole chiudere troppo presto
    if out.get('operation') == 'close':
        symbol_to_close = out.get('symbol', '')
        epic_to_close = f"{symbol_to_close}USD"
        
        # Cerca la posizione aperta
        position_to_check = None
        for pos in positions:
            pos_symbol = pos.get('symbol') or pos.get('epic', '')
            if pos_symbol == epic_to_close or pos_symbol == symbol_to_close:
                position_to_check = pos
                break
        
        if position_to_check:
            # Calcola quanto tempo è aperta la posizione
            opened_at = position_to_check.get('opened_at')
            pnl_pct = position_to_check.get('pnl_pct', 0) or 0
            
            # Verifica se possiamo chiudere
            can_close = False
            override_reason = None
            
            # Sempre permetti chiusura se stop loss o take profit significativo
            if pnl_pct <= STOP_LOSS_THRESHOLD_PCT:
                can_close = True
                override_reason = f"Stop loss triggered (PnL: {pnl_pct:.2f}%)"
            elif pnl_pct >= TAKE_PROFIT_THRESHOLD_PCT:
                can_close = True
                override_reason = f"Take profit triggered (PnL: {pnl_pct:.2f}%)"
            elif opened_at:
                # Controlla tempo minimo
                try:
                    if isinstance(opened_at, str):
                        opened_at = datetime.fromisoformat(opened_at.replace('Z', '+00:00'))
                    time_held = datetime.now(timezone.utc) - opened_at
                    minutes_held = time_held.total_seconds() / 60
                    
                    if minutes_held >= MIN_POSITION_HOLD_MINUTES:
                        can_close = True
                        override_reason = f"Position held for {minutes_held:.0f} min (>= {MIN_POSITION_HOLD_MINUTES} min)"
                    else:
                        print(f"   ⏳ ANTI-OVERTRADING: Posizione aperta da {minutes_held:.0f} min")
                        print(f"      Minimo richiesto: {MIN_POSITION_HOLD_MINUTES} min")
                        print(f"      PnL: {pnl_pct:.2f}% (stop loss: {STOP_LOSS_THRESHOLD_PCT}%, take profit: {TAKE_PROFIT_THRESHOLD_PCT}%)")
                except Exception as e:
                    print(f"   ⚠️ Errore calcolo tempo: {e}")
                    can_close = True  # In caso di errore, permetti
            else:
                # Nessuna info su opened_at, controlla l'ultima operazione nel DB
                can_close = True  # Default: permetti
            
            if not can_close:
                # Override: forza HOLD invece di CLOSE
                print(f"   🛑 OVERRIDE: Cambio 'close' -> 'hold' per evitare overtrading")
                out['operation'] = 'hold'
                out['reason'] = f"[ANTI-OVERTRADING] Position too young. Original: {out.get('reason', '')[:100]}"
            else:
                if override_reason:
                    print(f"   ✅ Chiusura permessa: {override_reason}")
    
    # 10. Esecuzione segnale
    print("\n9️⃣ Esecuzione segnale...")
    exec_result = bot.execute_signal(out)
    
    # 11. Logging
    print("\n🔟 Salvataggio nel database...")
    op_id = db_utils.log_bot_operation(
        out, 
        system_prompt=system_prompt, 
        indicators=indicators_json, 
        news_text=news_txt, 
        sentiment=sentiment_json, 
        forecasts=forecasts_json
    )
    print(f"   ✅ Operazione salvata con id={op_id}")

    print("\n" + "="*60)
    print("✅ CICLO COMPLETATO")
    print("="*60)

except Exception as e:
    print(f"\n❌ ERRORE: {e}")
    import traceback
    traceback.print_exc()
    
    # Log error to database
    try:
        db_utils.log_error(
            e, 
            context={
                "prompt": system_prompt, 
                "tickers": TICKERS,
                "indicators": indicators_json, 
                "news": news_txt,
                "sentiment": sentiment_json, 
                "forecasts": forecasts_json,
                "balance": account_status
            }, 
            source="trading_agent"
        )
    except:
        pass
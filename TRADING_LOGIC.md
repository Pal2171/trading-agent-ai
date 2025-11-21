# 🤖 Trading Agent - Logica di Funzionamento

## 📊 Analisi ogni 15 minuti

Il bot esegue un'analisi completa ogni 15 minuti su BTC, ETH, SOL.

### Indicatori Analizzati

1. **Supertrend** (principale filtro trend)
2. **EMA** (9, 20, 21, 50 periodi)
3. **RSI** (7 e 14 periodi)
4. **MACD** (momentum)
5. **ADX** (forza del trend)
6. **ATR** (volatilità)
7. **Candlestick Patterns** (Doji, Hammer, Engulfing, Morning/Evening Star)
8. **Volume** (Bid/Ask dall'orderbook)

### Dati di Contesto

- **News Feed**: Notizie crypto recenti
- **Sentiment Analysis**: Fear & Greed Index
- **Forecast**: Previsioni prezzi

---

## 🎯 Logica Decisionale

### OPEN LONG
✅ Supertrend BULLISH  
✅ Prezzo > EMA 20 > EMA 50  
✅ RSI 30-70 (non overbought)  
✅ Pattern rialzista (Hammer, Bullish Engulfing)  
✅ News positive  
✅ ADX > 20  

### OPEN SHORT
✅ Supertrend BEARISH  
✅ Prezzo < EMA 20 < EMA 50  
✅ RSI 30-70 (non oversold)  
✅ Pattern ribassista (Shooting Star, Bearish Engulfing)  
✅ News negative  
✅ ADX > 20  

### CLOSE POSITION
🚨 **OBBLIGATORIO**: Supertrend cambia direzione  
⚠️ Pattern di inversione forte  
⚠️ RSI estremo (>80 per long, <20 per short)  
⚠️ Breaking news contrarie  
✅ Target profit raggiunto  

---

## 💰 Gestione Leva (1x - 5x)

### 1x-2x - Conservativo
- ADX < 20 (trend debole)
- News miste
- Segnali conflittuali
- Alta volatilità

### 3x - Standard
- ADX 20-30
- Indicatori allineati
- Condizioni normali

### 4x-5x - Aggressivo
- ADX > 30 (trend forte)
- TUTTI indicatori allineati
- Pattern candlestick forte
- News supportive
- Volume sopra media
- Forecast conferma direzione

---

## 🛡️ Stop Loss & Trailing Stop

### Stop Loss Iniziale
- **2.5%** dal prezzo di entrata
- **Volatility-adjusted**: 2x ATR se maggiore

### Posizioni in LONG
- **Stop sotto**: swing low recente o Supertrend lower band

### Posizioni in SHORT
- **Stop sopra**: swing high recente o Supertrend upper band

### Trailing Stop Dinamico

| P&L % | Strategia |
|-------|-----------|
| 0-3% | Stop Loss fisso 2.5% |
| 3-5% | Move stop to break-even |
| >5% | Trailing stop 2% dal prezzo corrente |

### 🚨 Exit Automatici

1. **Supertrend Flip**: Chiusura IMMEDIATA della posizione
2. **Pattern di inversione**: Doji, Shooting Star, Bearish Engulfing
3. **Breaking News**: Notizie che contraddicono la posizione

---

## 📝 Output dell'AI

Ogni decisione include:

```json
{
  "operation": "open|close|hold",
  "symbol": "BTC|ETH|SOL",
  "direction": "long|short",
  "target_portion_of_balance": 0.3,
  "leverage": 3,
  "reason": "
    1. Perché questa decisione (indicatori specifici)
    2. Confronto con dati 15min precedenti
    3. Giustificazione leva
    4. Livello stop-loss raccomandato (prezzo specifico)
    5. Strategia trailing stop
    6. Considerazioni news/sentiment
  "
}
```

---

## 🔄 Frequenza di Aggiornamento

- **Analisi**: Ogni 15 minuti
- **Stop Loss**: Aggiornato ad ogni ciclo
- **Trailing Stop**: Spostato quando profitto > 3%
- **Supertrend Check**: Ogni ciclo (exit immediato se flip)

---

## ⚙️ Configurazione Attuale

- **Exchange**: Hyperliquid (Testnet)
- **Ticker**: BTC, ETH, SOL
- **Timeframe**: 15 minuti
- **Database**: PostgreSQL su Railway
- **AI Model**: Anthropic Claude (via `trading_agent.py`)

---

## 🚀 Avvio

```powershell
cd "g:\Il mio Drive\Github Progetti\trading-agent-ai"
python main.py
```

Il bot inizierà ad analizzare il mercato e prendere decisioni automaticamente.

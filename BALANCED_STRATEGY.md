# 🎯 Strategia Bilanciata - Anti-Overfitting

## Problema Overfitting
Se richiediamo TUTTI gli indicatori allineati, il sistema non genererà MAI segnali o solo raramente in condizioni "perfette" che potrebbero non ripetersi.

## Soluzione: Sistema a 3 Livelli

### ✅ LIVELLO 1: OBBLIGATORIO (Filtro Base)
Solo 2 condizioni **SEMPRE** richieste:
1. **Supertrend** nella direzione corretta (BULLISH per LONG, BEARISH per SHORT)
2. **Prezzo vs EMA 20** coerente (Sopra per LONG, Sotto per SHORT)

✨ Questo è SUFFICIENTE per aprire un trade a **1x-2x leverage**

### 📊 LIVELLO 2: PREFERITO (Miglioramento Qualità)
Servono almeno **2 di questi** per aumentare confidenza:
- EMA 20 vs EMA 50 allineate
- RSI non estremo (<70 per long, >30 per short)
- Pattern candlestick favorevole
- MACD momentum positivo/negativo
- Volume sopra media
- News sentiment favorevole

Con 2+ fattori preferiti → **2x-3x leverage**

### 🚀 LIVELLO 3: BONUS (Leva Massima)
Fattori che portano a **4x-5x leverage**:
- ADX > 25 (trend forte)
- Pattern candlestick molto forte (Engulfing, Morning/Evening Star)
- Forecast conferma direzione
- Volume molto alto (>1.5x media)
- Allineamento perfetto EMA 9 < 20 < 50

---

## 📈 Sistema di Scoring Leva

**Partenza Base**: 2x (se OBBLIGATORI soddisfatti)

**+1x per ogni:**
- ADX > 25
- Pattern candlestick forte
- EMA perfettamente allineate
- Volume alto
- Forecast conferma
- RSI in zona ottimale (40-60)

**-1x per ogni:**
- ADX < 15 (trend debole)
- News negative
- RSI estremo (>75 o <25)
- Volume basso

**Range finale**: 1x → 5x

---

## 🛡️ Stop Loss Bilanciati

### Stop Loss Iniziale
- **3.5%** (era 2.5% - ora più permissivo)
- **2.5x ATR** (era 2x - più spazio su volatili)
- **Max 6%** anche su asset molto volatili

### Trailing Stop
- **0-2% profit**: Stop iniziale (nessun cambio)
- **2-4% profit**: Break-even
- **4-6% profit**: Lock 2% profit
- **>6% profit**: Trail 3% dal picco

### Exit Automatici
- **OBBLIGATORIO**: Supertrend flip
- **Raccomandato**: Price cross EMA 20 + reversal candle
- **Considerare**: RSI estremo + divergenza, pattern inversione multipli

---

## ⚖️ Vantaggi Sistema Bilanciato

✅ **Genera segnali regolarmente** (no overfitting)  
✅ **Filtra comunque le peggiori operazioni** (Supertrend + EMA)  
✅ **Scala il rischio** in base alla qualità del setup  
✅ **Stop loss ragionevoli** (non troppo stretti)  
✅ **Flessibile** ma disciplinato  

---

## 📊 Esempi Pratici

### Trade Minimo (1x-2x)
- Supertrend BULLISH ✓
- Prezzo > EMA 20 ✓
- EMA 20 < EMA 50 ✗ (ancora in correzione)
- RSI 55 (ok ma non ottimale)
- No pattern candlestick forte
- News neutre

→ **Apri LONG 2x leverage** con stop 3.5%

### Trade Buono (3x)
- Supertrend BULLISH ✓
- Prezzo > EMA 20 ✓
- EMA 20 > EMA 50 ✓ (trend confermato)
- RSI 52 ✓ (zona ideale)
- Hammer bullish ✓
- Volume alto ✓

→ **Apri LONG 3x leverage** con stop 3%

### Trade Eccellente (4x-5x)
- Supertrend BULLISH ✓
- Prezzo > EMA 20 ✓
- EMA 9 < 20 < 50 ✓ (tutte allineate)
- ADX 32 ✓ (trend forte)
- Bullish Engulfing ✓ (pattern forte)
- Volume 2x media ✓
- News positive ✓
- Forecast +5% ✓

→ **Apri LONG 5x leverage** con stop 3%

---

## 🎓 Filosofia

> "Better to take good trades regularly with proper risk management, than to wait forever for the 'perfect' setup that never comes."

Il trading non è matematica perfetta, è gestione delle probabilità.

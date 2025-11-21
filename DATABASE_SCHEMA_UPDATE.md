# 📊 Aggiornamenti Database - Schema Indicatori

## Modifiche Apportate

### ✅ Nuovi Campi Aggiunti a `indicators_contexts`

| Campo | Tipo | Descrizione |
|-------|------|-------------|
| `ema9` | NUMERIC(20, 8) | EMA a 9 periodi |
| `ema21` | NUMERIC(20, 8) | EMA a 21 periodi |
| `supertrend` | TEXT | Direzione Supertrend (BULLISH/BEARISH) |
| `adx` | NUMERIC(20, 8) | Average Directional Index (forza trend) |
| `rsi_14` | NUMERIC(20, 8) | RSI a 14 periodi (già esistente ma ora valorizzato) |
| `candlestick_patterns` | JSONB | Pattern candlestick rilevati |

### ⚠️ Campi Deprecati (ma mantenuti per compatibilità)

| Campo | Stato | Note |
|-------|-------|------|
| `pp`, `s1`, `s2`, `r1`, `r2` | DEPRECATED | Pivot points rimossi dalla logica ma mantenuti nel DB |

Questi campi non vengono più popolati ma rimangono nello schema per non rompere query esistenti.

---

## 🗂️ Schema Completo `indicators_contexts`

```sql
CREATE TABLE indicators_contexts (
    -- Identificazione
    id                      BIGSERIAL PRIMARY KEY,
    context_id              BIGINT NOT NULL,
    ticker                  TEXT NOT NULL,
    ts                      TIMESTAMPTZ,
    
    -- Prezzi e EMA
    price                   NUMERIC(20, 8),
    ema9                    NUMERIC(20, 8),      -- NUOVO
    ema20                   NUMERIC(20, 8),
    ema21                   NUMERIC(20, 8),      -- NUOVO
    
    -- Indicatori Trend
    supertrend              TEXT,                -- NUOVO (BULLISH/BEARISH)
    adx                     NUMERIC(20, 8),      -- NUOVO
    
    -- Momentum
    macd                    NUMERIC(20, 8),
    rsi_7                   NUMERIC(20, 8),
    rsi_14                  NUMERIC(20, 8),
    
    -- Volume e Derivati
    volume_bid              NUMERIC(20, 8),
    volume_ask              NUMERIC(20, 8),
    open_interest_latest    NUMERIC(30, 10),
    open_interest_average   NUMERIC(30, 10),
    funding_rate            NUMERIC(20, 8),
    
    -- Timeframe 15m
    ema20_15m               NUMERIC(20, 8),
    ema50_15m               NUMERIC(20, 8),
    atr3_15m                NUMERIC(20, 8),
    atr14_15m               NUMERIC(20, 8),
    volume_15m_current      NUMERIC(30, 10),
    volume_15m_average      NUMERIC(30, 10),
    
    -- Pattern e Serie Temporali
    candlestick_patterns    JSONB,               -- NUOVO
    intraday_mid_prices     JSONB,
    intraday_ema20_series   JSONB,
    intraday_macd_series    JSONB,
    intraday_rsi7_series    JSONB,
    intraday_rsi14_series   JSONB,
    lt15m_macd_series       JSONB,
    lt15m_rsi14_series      JSONB,
    
    -- Pivot Points (DEPRECATED)
    pp                      NUMERIC(20, 8),
    s1                      NUMERIC(20, 8),
    s2                      NUMERIC(20, 8),
    r1                      NUMERIC(20, 8),
    r2                      NUMERIC(20, 8)
);
```

---

## 📝 Esempio Dati Salvati

### Candlestick Patterns (JSONB)

```json
{
  "patterns": [
    {
      "name": "Hammer",
      "type": "reversal",
      "signal": "bullish",
      "description": "Possibile inversione rialzista, pressione acquisto"
    },
    {
      "name": "Bullish Engulfing",
      "type": "reversal",
      "signal": "bullish",
      "description": "Forte segnale rialzista, buyers prendono controllo"
    }
  ],
  "interpretation": "BULLISH - 2 pattern rialzisti rilevati",
  "total_patterns": 2
}
```

### Supertrend (TEXT)
```
"BULLISH"  oppure  "BEARISH"
```

---

## 🔄 Migrazione Automatica

Il sistema esegue automaticamente le migrazioni all'avvio tramite `init_db()`:

```python
# In main.py o script di inizializzazione
from db_utils import init_db

init_db()  # Crea/aggiorna schema automaticamente
```

Le migration sono **idempotenti** (`ADD COLUMN IF NOT EXISTS`), quindi possono essere eseguite multiple volte senza errori.

---

## ✅ Compatibilità

- **Vecchie query**: Continuano a funzionare (campi deprecati presenti)
- **Nuove query**: Possono accedere ai nuovi campi
- **Dati esistenti**: I nuovi campi saranno NULL per record vecchi
- **Nessun downtime**: Le migration si applicano senza interruzioni

---

## 🔍 Query Utili

### Recupera ultimi indicatori con candlestick patterns
```sql
SELECT 
    ticker,
    ts,
    price,
    supertrend,
    adx,
    ema9,
    ema20,
    ema21,
    candlestick_patterns
FROM indicators_contexts
ORDER BY ts DESC
LIMIT 10;
```

### Trova tutti i trade con pattern Engulfing
```sql
SELECT 
    ic.ticker,
    ic.ts,
    ic.candlestick_patterns,
    bo.operation,
    bo.leverage
FROM indicators_contexts ic
JOIN bot_operations bo ON ic.context_id = bo.context_id
WHERE ic.candlestick_patterns::text LIKE '%Engulfing%'
ORDER BY ic.ts DESC;
```

### Analisi performance per Supertrend
```sql
SELECT 
    ic.supertrend,
    COUNT(*) as trades,
    AVG(op.leverage) as avg_leverage,
    COUNT(CASE WHEN op.operation = 'open' THEN 1 END) as opens
FROM indicators_contexts ic
JOIN bot_operations op ON ic.context_id = op.context_id
GROUP BY ic.supertrend;
```

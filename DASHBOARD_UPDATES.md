# 📊 Aggiornamenti Dashboard - Nuovi Campi Database

## ⚠️ Breaking Changes per Dashboard

La dashboard deve essere aggiornata per gestire i nuovi campi nella tabella `indicators_contexts`.

---

## 🔄 Modifiche al Database

### Campi Aggiunti

```sql
-- Nuovi campi disponibili
ema9                    NUMERIC(20, 8)      -- EMA a 9 periodi
ema21                   NUMERIC(20, 8)      -- EMA a 21 periodi
supertrend              TEXT                -- "BULLISH" o "BEARISH"
adx                     NUMERIC(20, 8)      -- Forza del trend (0-100)
rsi_14                  NUMERIC(20, 8)      -- RSI a 14 periodi
candlestick_patterns    JSONB               -- Pattern rilevati
```

### Campi Deprecati (ancora presenti ma NULL)

```sql
-- Non più popolati ma mantenuti per compatibilità
pp, s1, s2, r1, r2      NUMERIC(20, 8)      -- Pivot points
```

---

## 📝 Query Aggiornate

### Query Base Indicatori (PRIMA)

```sql
SELECT 
    ticker,
    ts,
    price,
    ema20,
    macd,
    rsi_7,
    pp, s1, s2, r1, r2  -- ❌ Deprecati
FROM indicators_contexts
ORDER BY ts DESC;
```

### Query Base Indicatori (DOPO)

```sql
SELECT 
    ticker,
    ts,
    price,
    ema9,           -- ✅ NUOVO
    ema20,
    ema21,          -- ✅ NUOVO
    supertrend,     -- ✅ NUOVO (TEXT)
    adx,            -- ✅ NUOVO
    macd,
    rsi_7,
    rsi_14,         -- ✅ NUOVO
    candlestick_patterns  -- ✅ NUOVO (JSONB)
FROM indicators_contexts
ORDER BY ts DESC;
```

---

## 🎨 Componenti Dashboard da Aggiornare

### 1. Visualizzazione Indicatori

**Prima:**
```javascript
// Esempio React/Next.js
<div>
  <span>EMA 20: {indicator.ema20}</span>
  <span>RSI: {indicator.rsi_7}</span>
  <span>Pivot: {indicator.pp}</span>  {/* ❌ Da rimuovere */}
</div>
```

**Dopo:**
```javascript
<div>
  <span>EMA 9: {indicator.ema9}</span>
  <span>EMA 20: {indicator.ema20}</span>
  <span>EMA 21: {indicator.ema21}</span>
  <span>Supertrend: 
    <Badge color={indicator.supertrend === 'BULLISH' ? 'green' : 'red'}>
      {indicator.supertrend}
    </Badge>
  </span>
  <span>ADX: {indicator.adx.toFixed(1)} 
    {indicator.adx > 25 ? ' 🔥 Strong' : ' ⚠️ Weak'}
  </span>
  <span>RSI(7): {indicator.rsi_7}</span>
  <span>RSI(14): {indicator.rsi_14}</span>
</div>
```

### 2. Candlestick Patterns (NUOVO)

```javascript
// Componente per mostrare pattern candlestick
function CandlestickPatterns({ patterns }) {
  if (!patterns || !patterns.patterns || patterns.patterns.length === 0) {
    return <span>No patterns</span>;
  }

  return (
    <div className="candlestick-patterns">
      <h4>{patterns.interpretation}</h4>
      <ul>
        {patterns.patterns.map((pattern, idx) => (
          <li key={idx}>
            <span className={`badge badge-${pattern.signal}`}>
              {pattern.name}
            </span>
            - {pattern.description}
          </li>
        ))}
      </ul>
    </div>
  );
}

// Uso nel componente principale
<CandlestickPatterns patterns={indicator.candlestick_patterns} />
```

### 3. Supertrend Indicator (NUOVO)

```javascript
// Badge/Chip per Supertrend
function SupertrendBadge({ supertrend }) {
  const isBullish = supertrend === 'BULLISH';
  
  return (
    <span className={`supertrend ${isBullish ? 'bullish' : 'bearish'}`}>
      {isBullish ? '🟢' : '🔴'} {supertrend}
    </span>
  );
}

// CSS
.supertrend.bullish {
  background: #10b981;
  color: white;
  padding: 4px 12px;
  border-radius: 16px;
}

.supertrend.bearish {
  background: #ef4444;
  color: white;
  padding: 4px 12px;
  border-radius: 16px;
}
```

### 4. ADX Strength Meter (NUOVO)

```javascript
function ADXStrengthMeter({ adx }) {
  let strength = 'Weak';
  let color = 'gray';
  
  if (adx > 25) {
    strength = 'Strong';
    color = 'green';
  } else if (adx > 15) {
    strength = 'Moderate';
    color = 'yellow';
  }
  
  return (
    <div className="adx-meter">
      <span>ADX: {adx.toFixed(1)}</span>
      <div className="progress-bar">
        <div 
          className={`progress-fill ${color}`}
          style={{ width: `${Math.min(adx, 50)}%` }}
        />
      </div>
      <span className={`strength-label ${color}`}>{strength}</span>
    </div>
  );
}
```

---

## 🗂️ API Endpoints da Aggiornare

### Backend (Python/Flask/FastAPI)

```python
# Esempio endpoint Flask
@app.route('/api/indicators/latest')
def get_latest_indicators():
    query = """
        SELECT 
            ticker,
            ts,
            price,
            ema9, ema20, ema21,
            supertrend,
            adx,
            macd,
            rsi_7, rsi_14,
            candlestick_patterns
        FROM indicators_contexts
        WHERE ts > NOW() - INTERVAL '1 hour'
        ORDER BY ts DESC
        LIMIT 100;
    """
    
    results = db.execute(query)
    
    return jsonify([{
        'ticker': r.ticker,
        'timestamp': r.ts.isoformat(),
        'price': float(r.price),
        'ema': {
            'ema9': float(r.ema9) if r.ema9 else None,
            'ema20': float(r.ema20) if r.ema20 else None,
            'ema21': float(r.ema21) if r.ema21 else None,
        },
        'supertrend': r.supertrend,
        'adx': float(r.adx) if r.adx else None,
        'macd': float(r.macd) if r.macd else None,
        'rsi': {
            'rsi_7': float(r.rsi_7) if r.rsi_7 else None,
            'rsi_14': float(r.rsi_14) if r.rsi_14 else None,
        },
        'candlestick_patterns': r.candlestick_patterns  # Già JSON
    } for r in results])
```

### Backend (Node.js/Express)

```javascript
// Esempio endpoint Express
app.get('/api/indicators/latest', async (req, res) => {
  const result = await pool.query(`
    SELECT 
      ticker,
      ts,
      price,
      ema9, ema20, ema21,
      supertrend,
      adx,
      macd,
      rsi_7, rsi_14,
      candlestick_patterns
    FROM indicators_contexts
    WHERE ts > NOW() - INTERVAL '1 hour'
    ORDER BY ts DESC
    LIMIT 100
  `);
  
  const indicators = result.rows.map(row => ({
    ticker: row.ticker,
    timestamp: row.ts,
    price: parseFloat(row.price),
    ema: {
      ema9: parseFloat(row.ema9),
      ema20: parseFloat(row.ema20),
      ema21: parseFloat(row.ema21),
    },
    supertrend: row.supertrend,
    adx: parseFloat(row.adx),
    macd: parseFloat(row.macd),
    rsi: {
      rsi_7: parseFloat(row.rsi_7),
      rsi_14: parseFloat(row.rsi_14),
    },
    candlestickPatterns: row.candlestick_patterns
  }));
  
  res.json(indicators);
});
```

---

## 📊 Nuove Visualizzazioni Consigliate

### 1. Dashboard Card - Supertrend Status

```
┌─────────────────────────────┐
│ BTC/USD                     │
│ $95,609.00        🟢 BULLISH│
│                             │
│ ADX: 32.5 (Strong Trend)    │
│ ━━━━━━━━━━━━━━━━━━━━━━━    │
│                             │
│ Candlestick: BULLISH        │
│ • Hammer (bullish)          │
│ • Volume spike              │
└─────────────────────────────┘
```

### 2. Trend Strength Indicator

```javascript
{
  ticker: 'BTC',
  supertrend: 'BULLISH',
  adx: 32.5,
  ema_alignment: true,  // ema9 < ema20 < ema21
  confidence: 'HIGH'    // Calcolato lato dashboard
}
```

### 3. Pattern History Table

```
| Time     | Ticker | Pattern           | Signal  | Outcome |
|----------|--------|-------------------|---------|---------|
| 14:30    | BTC    | Bullish Engulfing | Bullish | +2.3%   |
| 14:15    | ETH    | Doji              | Neutral | -0.1%   |
| 14:00    | SOL    | Shooting Star     | Bearish | -1.5%   |
```

---

## ✅ Checklist Aggiornamento Dashboard

- [ ] Aggiornare query SQL per includere nuovi campi
- [ ] Rimuovere riferimenti ai pivot points (pp, s1, s2, r1, r2)
- [ ] Aggiungere componente Supertrend badge
- [ ] Aggiungere componente ADX strength meter
- [ ] Aggiungere visualizzazione candlestick patterns
- [ ] Aggiungere EMA 9 e 21 ai grafici
- [ ] Testare con dati reali dal database aggiornato
- [ ] Aggiornare TypeScript types/interfaces (se applicabile)
- [ ] Aggiornare documentazione API
- [ ] Deploy su Railway

---

## 🔗 Link Utili

- **Database Schema**: Vedi `DATABASE_SCHEMA_UPDATE.md`
- **Query Esempi**: Vedi sezione "Query Utili" nel documento schema

---

## ⚙️ Variabili d'Ambiente

Assicurati che la dashboard abbia accesso al database:

```env
DATABASE_URL=postgresql://postgres:wvmvOXMEYMHgHhtbLDrOZSuuLLFZlrts@caboose.proxy.rlwy.net:25756/railway
```

(Stesso URL del trading bot)

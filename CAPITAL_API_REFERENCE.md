# Capital.com API - Riferimento Completo

## 📋 Informazioni Generali

- **Base URL (Live):** `https://api-capital.backend-capital.com/`
- **Base URL (Demo):** `https://demo-api-capital.backend-capital.com/`
- **WebSocket:** `wss://api-streaming-capital.backend-capital.com/connect`
- **Sessione attiva:** 10 minuti (inattività massima)

## 🔐 Autenticazione

### Creare sessione
**Endpoint:** `POST /api/v1/session`

**Headers:**
- `X-CAP-API-KEY`: API key da Settings > API Integrations

**Body:**
```json
{
  "identifier": "YOUR_EMAIL",
  "password": "YOUR_API_KEY_PASSWORD",
  "encryptedPassword": false
}
```

**Response Headers (da salvare):**
- `CST`: Authorization token (valido 10 minuti)
- `X-SECURITY-TOKEN`: Account token

**Limiti:**
- 1 richiesta/secondo per questo endpoint
- Max 1000 richieste/ora in Demo per POST /positions e POST /workingorders

## 📊 Trading - Positions

### Aprire Posizione
**Endpoint:** `POST /api/v1/positions`

**Headers obbligatori:**
- `CST`: Token di autorizzazione
- `X-SECURITY-TOKEN`: Token account

**Body Parameters:**

| Parametro | Tipo | Obbligatorio | Descrizione |
|-----------|------|--------------|-------------|
| `epic` | string | ✅ YES | Identificatore strumento (es. "EURUSD", "US500", "BTCUSD") |
| `direction` | string | ✅ YES | "BUY" o "SELL" |
| `size` | number | ✅ YES | Dimensione ordine (units per forex, contracts per altri) |
| `guaranteedStop` | boolean | ❌ NO | Default: false. Se true richiede stopLevel/stopDistance/stopAmount |
| `trailingStop` | boolean | ❌ NO | Default: false. Se true richiede stopDistance. Non compatibile con guaranteedStop |
| `stopLevel` | number | ❌ NO | Prezzo assoluto di stop loss |
| `stopDistance` | number | ❌ NO | Distanza tra prezzo corrente e stop loss trigger |
| `stopAmount` | number | ❌ NO | Perdita in valuta quando stop loss si attiva |
| `profitLevel` | number | ❌ NO | Prezzo assoluto di take profit |
| `profitDistance` | number | ❌ NO | Distanza tra prezzo corrente e take profit trigger |
| `profitAmount` | number | ❌ NO | Profitto in valuta quando take profit si attiva |

**Response:**
```json
{
  "dealReference": "o_98c0de50-9cd5-4481-8d81-890c525eeb49"
}
```

**Note critiche:**
- Response con status 200 NON garantisce apertura posizione!
- Usare `GET /api/v1/confirms/{dealReference}` per conferma
- Stop/Profit non disponibili per azioni reali
- Trailing stop incompatibile con guaranteed stop e hedging mode

### Confermare Ordine/Posizione
**Endpoint:** `GET /api/v1/confirms/{dealReference}`

**Response:**
```json
{
  "date": "2022-04-06T07:32:19.193",
  "status": "OPEN",
  "dealStatus": "ACCEPTED",
  "epic": "SILVER",
  "dealId": "006011e7-0001-54c4-0000-000080560043",
  "affectedDeals": [
    {
      "dealId": "...",
      "status": "OPENED"
    }
  ],
  "level": 24.285,
  "size": 1,
  "direction": "BUY",
  "stopLevel": 20.0,
  "profitLevel": 27.0
}
```

**Deal Status possibili:**
- `ACCEPTED`: Ordine accettato
- `REJECTED`: Ordine rifiutato
- `OPEN`: Posizione aperta

### Ottenere Posizioni Aperte
**Endpoint:** `GET /api/v1/positions`

**Response:**
```json
{
  "positions": [
    {
      "position": {
        "dealId": "...",
        "size": 1,
        "direction": "BUY",
        "level": 21.059,
        "createdDate": "2022-04-06T10:49:52.056",
        "upl": -0.022
      },
      "market": {
        "epic": "SILVER",
        "bid": 21.037,
        "offer": 21.057
      }
    }
  ]
}
```

### Chiudere Posizione
**Endpoint:** `DELETE /api/v1/positions/{dealId}`

**Response:**
```json
{
  "dealReference": "p_006011e7-0001-54c4-0000-000080560068"
}
```

## 🎯 Dealing Rules per Strumento

### EURUSD (Forex)
- **Min Deal Size:** 1000 units (demo account)
- **Min Increment:** Variabile (Capital.com arrotonda automaticamente a 100)
- **Size rounding:** Arrotondare a centinaia (1000, 1100, 1200...)
- **Stop/Profit Distance:** In valuta base (USD per EURUSD)
- **Esempio:**
  ```python
  size = round(size / 100) * 100  # Arrotonda a 100
  if size < 1000:
      size = 1000
  ```

### US500 (Index)
- **Min Deal Size:** 0.1 contracts (demo account)
- **Min Increment:** 0.01
- **Size rounding:** 2 decimali
- **Stop/Profit Distance:** In punti index
- **Esempio:**
  ```python
  size = round(size, 2)
  if size < 0.1:
      size = 0.1
  ```

### BTCUSD (Crypto)
- **Min Deal Size:** 0.0001 BTC
- **Min Increment:** 0.0001
- **Size rounding:** 4 decimali
- **Stop/Profit Distance:** In USD
- **Esempio:**
  ```python
  size = round(size, 4)
  if size < 0.0001:
      size = 0.0001
  ```

## 🚨 Errori Comuni

### `error.invalid.request`
**Cause possibili:**
1. **Size non conforme ai dealing rules:**
   - EURUSD: size non multiplo di 100 o < 1000
   - US500: size < 0.1 in demo
   - BTCUSD: size < 0.0001

2. **Stop/Profit Distance invalida:**
   - Troppo vicina al prezzo corrente
   - Troppo lontana (superato max distance)
   - Non rispetta minStepDistance

3. **Trailing Stop incompatibile:**
   - Usato insieme a guaranteedStop
   - Usato in hedging mode
   - Manca stopDistance quando trailingStop=true

4. **Mercato non tradeable:**
   - Mercato chiuso (weekend, festivi)
   - Strumento sospeso

### `error.position.cannot-create-position`
- Account non ha fondi sufficienti
- Max posizioni raggiunto
- Leverage non sufficiente

### `error.security.invalid-details`
- CST o X-SECURITY-TOKEN scaduto (> 10 min inattività)
- Rifare POST /session per nuovi token

## 📐 Calcolo Size Corretto

### Formula base:
```python
# 1. Calcola amount in USD
amount_usd = account_balance * portion  # es. 10000 * 0.15 = 1500

# 2. Dividi per prezzo corrente
size = amount_usd / current_price  # es. 1500 / 1.05 = 1428.57

# 3. Applica rounding specifico per ticker
if ticker == 'EURUSD':
    size = round(size / 100) * 100  # 1428.57 → 1400
    if size < 1000:
        size = 1000
elif ticker == 'US500':
    size = round(size, 2)
    if size < 0.1:
        size = 0.1
elif ticker == 'BTCUSD':
    size = round(size, 4)
    if size < 0.0001:
        size = 0.0001
```

### ⚠️ NON moltiplicare per leverage!
Capital.com applica leverage automaticamente via margin. Il size deve essere in units/contracts reali.

## 📏 Stop Loss e Take Profit

### Stop Distance (ATR-based)
```python
# Ottieni ATR da indicators
atr = indicators['longer_term_15m']['atr_14_current']

# Calcola stop distance
stop_multiplier = 3 if ticker == 'BTCUSD' else 2
stop_distance = atr * stop_multiplier

# Take profit (Risk/Reward 1:2)
profit_distance = stop_distance * 2
```

### Valori risultanti (esempio):
- **EURUSD:** ATR 0.00234 → Stop 0.00468 → Profit 0.00936
- **US500:** ATR 134.47 → Stop 268.94 → Profit 537.88
- **BTCUSD:** ATR 1743.56 → Stop 5230.68 → Profit 10461.36

### Note:
- Capital.com accetta distanze in **valuta base** (non pip o percentuali)
- I valori vengono convertiti automaticamente in livelli assoluti
- `stopLevel` e `profitLevel` visibili nella conferma ordine

## 🔄 Trailing Stop

**Quando abilitare:**
- Setup STRONG (leverage >= 3)
- Mercato in trend forte
- Necessario monitoraggio dinamico stop loss

**Parametri:**
```python
trailing_stop = True
stop_distance = atr * 2  # OBBLIGATORIO se trailing_stop=True
# profitDistance opzionale
```

**Incompatibilità:**
- ❌ guaranteedStop = True
- ❌ hedgingMode = True

## 📈 Market Info

### Ottenere dettagli strumento
**Endpoint:** `GET /api/v1/markets/{epic}`

**Response (excerpt):**
```json
{
  "instrument": {
    "epic": "EURUSD",
    "marginFactor": 3.33,
    "marginFactorUnit": "PERCENTAGE"
  },
  "dealingRules": {
    "minDealSize": {
      "value": 1000
    },
    "minSizeIncrement": {
      "value": 100
    },
    "minStopOrProfitDistance": {
      "value": 0.6
    }
  },
  "snapshot": {
    "bid": 1.0537,
    "offer": 1.0538,
    "marketStatus": "TRADEABLE"
  }
}
```

### Ricerca strumenti
**Endpoint:** `GET /api/v1/markets?searchTerm=bitcoin`

Restituisce tutti gli strumenti che contengono "bitcoin" nel nome.

## 📊 Prezzi Storici

**Endpoint:** `GET /api/v1/prices/{epic}`

**Query Parameters:**
- `resolution`: MINUTE, MINUTE_5, MINUTE_15, MINUTE_30, HOUR, HOUR_4, DAY, WEEK
- `max`: Max 1000 valori
- `from`: Data inizio (YYYY-MM-DDTHH:MM:SS)
- `to`: Data fine

**Response:**
```json
{
  "prices": [
    {
      "snapshotTime": "2022-02-24T00:00:00",
      "openPrice": { "bid": 1.05, "ask": 1.051 },
      "closePrice": { "bid": 1.052, "ask": 1.053 },
      "highPrice": { "bid": 1.054, "ask": 1.055 },
      "lowPrice": { "bid": 1.049, "ask": 1.050 }
    }
  ]
}
```

## ⏰ Keep Session Alive

**Endpoint:** `GET /api/v1/ping`

Chiamare almeno ogni 10 minuti per mantenere attiva la sessione.

## 🎯 Best Practices

### 1. Sempre verificare conferma ordine
```python
# Apri posizione
result = execute_order(...)
deal_ref = result.get('dealReference')

# Attendi processing
time.sleep(0.5)

# Verifica stato
confirm = get_deal_confirmation(deal_ref)
if confirm['dealStatus'] == 'ACCEPTED':
    deal_id = confirm['dealId']
    # Posizione aperta con successo
```

### 2. Gestire sessione scaduta
```python
try:
    response = session.post(url, headers=headers, json=payload)
    if response.status_code == 401:
        # Ri-autentica
        authenticate()
        # Riprova richiesta
        response = session.post(url, headers=headers, json=payload)
except Exception as e:
    log_error(e)
```

### 3. Rispettare rate limits
- Max 10 richieste/secondo per user
- Max 1 richiesta ogni 0.1 secondi per POST /positions e /workingorders
- In Demo: Max 1000 POST /positions o /workingorders per ora

### 4. Arrotondare size PRIMA dell'invio
```python
# ✅ CORRETTO
size = round(size / 100) * 100
result = execute_order(epic, direction, size, ...)

# ❌ SBAGLIATO
result = execute_order(epic, direction, 1424.31, ...)  # Rifiutato!
```

### 5. Calcolare stop/profit in valuta assoluta
```python
# ✅ CORRETTO
stop_distance = atr * 2  # es. 0.00468 USD per EURUSD

# ❌ SBAGLIATO
stop_distance_pips = 46.8  # Capital.com non usa pips!
```

## 🐛 Debugging

### Check market status
```python
market = get_market_details(epic)
if market['snapshot']['marketStatus'] != 'TRADEABLE':
    print(f"Market {epic} not tradeable")
```

### Check dealing rules
```python
market = get_market_details(epic)
min_size = market['dealingRules']['minDealSize']['value']
min_increment = market['dealingRules']['minSizeIncrement']['value']
print(f"Min size: {min_size}, Increment: {min_increment}")
```

### Validate size before sending
```python
def validate_size(ticker, size):
    if ticker == 'EURUSD':
        if size < 1000:
            return False, "Size < 1000"
        if size % 100 != 0:
            return False, f"Size {size} not multiple of 100"
    elif ticker == 'US500':
        if size < 0.1:
            return False, "Size < 0.1"
    elif ticker == 'BTCUSD':
        if size < 0.0001:
            return False, "Size < 0.0001"
    return True, "OK"
```

## 📚 Riferimenti Utili

- **Documentazione ufficiale:** https://api-capital.backend-capital.com/
- **Postman Collection:** https://github.com/capital-com-sv/capital-api-postman
- **Java Samples:** https://github.com/capital-com-sv/api-java-samples
- **Support:** support@capital.com

---

**Ultima revisione:** 2025-11-25  
**Versione API:** 1.0.0

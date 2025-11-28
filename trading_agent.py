import google.generativeai as genai
from dotenv import load_dotenv
import os
import json

load_dotenv()

# Configurazione Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY non trovata nel file .env")

genai.configure(api_key=GEMINI_API_KEY)

# Schema JSON per Gemini con validazione nelle descrizioni
TRADE_SCHEMA = {
    "type": "object",
    "properties": {
        "operation": {
            "type": "string",
            "description": "Type of trading operation to perform: open, close, or hold",
            "enum": ["open", "close", "hold"]
        },
        "symbol": {
            "type": "string",
            "description": "The cryptocurrency symbol to act on: BTC, ETH, or SOL",
            "enum": ["BTC", "ETH", "SOL"]
        },
        "direction": {
            "type": "string",
            "description": "Trade direction: long (betting price goes up) or short (betting price goes down)",
            "enum": ["long", "short"]
        },
        "target_portion_of_balance": {
            "type": "number",
            "description": "Fraction of balance/position to use. MUST be between 0.0 and 1.0 (inclusive). For open: fraction of balance. For close: fraction of position."
        },
        "leverage": {
            "type": "number",
            "description": "Leverage multiplier. MUST be between 1 and 10 (inclusive). Higher leverage = higher risk and reward."
        },
        "reason": {
            "type": "string",
            "description": "Brief explanation of the trading decision. Maximum 300 characters."
        }
    },
    "required": [
        "operation",
        "symbol",
        "direction",
        "target_portion_of_balance",
        "leverage",
        "reason"
    ]
}

# Prompt di sistema per forzare la validazione
VALIDATION_INSTRUCTIONS = """
CRITICAL VALIDATION RULES - YOU MUST FOLLOW THESE EXACTLY:
1. target_portion_of_balance: MUST be a number between 0.0 and 1.0 (inclusive)
2. leverage: MUST be an integer between 1 and 10 (inclusive)
3. reason: MUST be maximum 300 characters
4. operation: MUST be one of: open, close, hold
5. symbol: MUST be one of: BTC, ETH, SOL
6. direction: MUST be one of: long, short

If any value is outside these ranges, adjust it to the nearest valid value.
"""

def previsione_trading_agent(prompt):
    """
    Utilizza Gemini 2.5 Pro per generare decisioni di trading strutturate.
    
    Args:
        prompt (str): Il prompt completo con tutte le informazioni di mercato
        
    Returns:
        dict: Decisione di trading in formato JSON strutturato e validato
    """
    try:
        # Aggiungi le istruzioni di validazione al prompt
        full_prompt = f"{VALIDATION_INSTRUCTIONS}\n\n{prompt}"
        
        # Inizializza il modello Gemini 2.5 Pro
        model = genai.GenerativeModel(
            model_name='gemini-2.5-pro',
            generation_config={
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 8192,
                "response_mime_type": "application/json",
                "response_schema": TRADE_SCHEMA
            }
        )
        
        # Genera la risposta
        response = model.generate_content(full_prompt)
        
        # Parse della risposta JSON
        result = json.loads(response.text)
        
        # Validazione post-processing (safety check)
        result = validate_trading_decision(result)
        
        print(f"[Gemini] Decisione: {result['operation']} {result.get('symbol', 'N/A')} {result.get('direction', 'N/A')}")
        
        return result
        
    except json.JSONDecodeError as e:
        print(f"[Errore] Risposta non valida da Gemini: {response.text}")
        raise ValueError(f"Gemini ha restituito JSON non valido: {e}")
    
    except Exception as e:
        print(f"[Errore] Chiamata a Gemini fallita: {e}")
        raise


def validate_trading_decision(decision):
    """
    Valida e corregge i valori della decisione di trading.
    
    Args:
        decision (dict): Decisione di trading da validare
        
    Returns:
        dict: Decisione validata e corretta
    """
    # Clamp target_portion_of_balance tra 0.0 e 1.0
    if 'target_portion_of_balance' in decision:
        decision['target_portion_of_balance'] = max(0.0, min(1.0, decision['target_portion_of_balance']))
    
    # Clamp leverage tra 1 e 10
    if 'leverage' in decision:
        decision['leverage'] = max(1, min(10, int(decision['leverage'])))
    
    # Tronca reason a 300 caratteri
    if 'reason' in decision and len(decision['reason']) > 300:
        decision['reason'] = decision['reason'][:297] + "..."
    
    return decision


def get_gemini_model_info():
    """
    Restituisce informazioni sul modello Gemini utilizzato.
    
    Returns:
        dict: Informazioni sul modello
    """
    return {
        "provider": "Google",
        "model_name": "gemini-2.5-pro",
        "model_display_name": "Gemini 2.5 Pro",
        "capabilities": [
            "JSON Schema Output",
            "Long Context (1M tokens)",
            "Advanced Reasoning (Thinking)",
            "Multimodal Support",
            "Complex Analysis"
        ],
        "temperature": 0.7,
        "max_tokens": 8192,
        "validation": "Post-processing validation for trading parameters"
    }


if __name__ == "__main__":
    # Test del modello
    info = get_gemini_model_info()
    print(f"\n{'='*60}")
    print(f"GEMINI MODEL INFO")
    print(f"{'='*60}")
    print(f"Provider: {info['provider']}")
    print(f"Model: {info['model_display_name']}")
    print(f"Model ID: {info['model_name']}")
    print(f"\nCapabilities:")
    for cap in info['capabilities']:
        print(f"  - {cap}")
    print(f"\nConfiguration:")
    print(f"  - Temperature: {info['temperature']}")
    print(f"  - Max Tokens: {info['max_tokens']}")
    print(f"  - Validation: {info['validation']}")
    print(f"{'='*60}\n")
    
    # Test con un prompt semplice
    test_prompt = """
    You are a crypto trading AI. Based on the following data, make a trading decision:
    
    BTC Price: $95,000
    Trend: Bullish
    RSI: 45 (neutral)
    Balance: $1000
    
    Respond with a JSON decision following the schema.
    """
    
    print("Testing Gemini API with sample prompt...")
    try:
        result = previsione_trading_agent(test_prompt)
        print(f"\n[OK] Test Result:")
        print(json.dumps(result, indent=2))
        print("\n[OK] Gemini API test successful!")
        print(f"\nValidation Check:")
        print(f"  - target_portion: {result['target_portion_of_balance']} (0.0-1.0)")
        print(f"  - leverage: {result['leverage']} (1-10)")
        print(f"  - reason length: {len(result['reason'])} chars (max 300)")
    except Exception as e:
        print(f"\n[ERROR] Gemini API test failed: {e}")
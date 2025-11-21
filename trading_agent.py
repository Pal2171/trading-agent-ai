from anthropic import Anthropic
from dotenv import load_dotenv
import os
import json 

load_dotenv()
# read api key
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY not found in .env")

client = Anthropic(api_key=ANTHROPIC_API_KEY)

def previsione_trading_agent(prompt):
    """
    Genera una decisione di trading usando Claude 4.5 Haiku.
    Il prompt deve contenere tutte le informazioni necessarie.
    """
    
    # Definizione dello schema JSON atteso (per il system prompt)
    json_schema = """
    {
        "operation": "open" | "close" | "hold",
        "symbol": "BTC" | "ETH" | "SOL",
        "direction": "long" | "short",
        "target_portion_of_balance": float (0.0 - 1.0),
        "leverage": int (1 - 5),
        "reason": "string (max 300 chars)"
    }
    """

    system_message = f"""Sei un esperto trader AI. Analizza i dati forniti e prendi una decisione di trading.
    DEVI rispondere ESCLUSIVAMENTE con un oggetto JSON valido che rispetta questo schema:
    {json_schema}
    
    Non aggiungere altro testo prima o dopo il JSON.
    """

    try:
        message = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=1024,
            temperature=0,
            system=system_message,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        # Estrazione del contenuto JSON
        response_text = message.content[0].text
        
        # Pulizia eventuale markdown (es. ```json ... ```)
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
            
        return json.loads(response_text)

    except Exception as e:
        print(f"Errore durante la chiamata ad Anthropic: {e}")
        # Ritorna un'azione di default sicura (HOLD)
        return {
            "operation": "hold",
            "symbol": "BTC",
            "direction": "long",
            "target_portion_of_balance": 0,
            "leverage": 1,
            "reason": f"Error calling AI: {str(e)}"
        }
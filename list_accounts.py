from capital_trader import CapitalTrader
import os
import requests
from dotenv import load_dotenv
load_dotenv()

bot = CapitalTrader(
    api_key=os.getenv('CAPITAL_API_KEY'),
    password=os.getenv('CAPITAL_API_PASSWORD'),
    identifier=os.getenv('CAPITAL_IDENTIFIER'),
    demo_mode=True
)

url = f'{bot.base_url}/api/v1/accounts'
headers = {'X-SECURITY-TOKEN': bot.x_security_token, 'CST': bot.cst}
resp = requests.get(url, headers=headers)

print("\n" + "="*70)
print("CAPITAL.COM ACCOUNTS")
print("="*70)
for acc in resp.json().get('accounts', []):
    acc_id = acc['accountId']
    name = acc['accountName']
    balance = acc['balance']['balance']
    currency = acc['currency']
    preferred = acc.get('preferred', False)
    print(f"  ID: {acc_id}")
    print(f"  Name: {name}")
    print(f"  Balance: {balance} {currency}")
    print(f"  Preferred: {preferred}")
    print("-"*70)

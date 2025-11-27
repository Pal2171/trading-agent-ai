#!/usr/bin/env python3
"""Test Capital.com API connection and basic operations"""

import os
from dotenv import load_dotenv
from capital_trader import CapitalTrader

load_dotenv()

def test_connection():
    print("=" * 60)
    print("🧪 TEST CAPITAL.COM API CONNECTION")
    print("=" * 60)
    
    # Get credentials
    api_key = os.getenv("CAPITAL_API_KEY")
    password = os.getenv("CAPITAL_API_PASSWORD")
    identifier = os.getenv("CAPITAL_IDENTIFIER")
    demo_mode = os.getenv("CAPITAL_DEMO_MODE", "True").lower() == "true"
    
    print(f"\n📧 Identifier: {identifier}")
    print(f"🔑 API Key: {api_key[:8]}...")
    print(f"🏷️ Mode: {'DEMO' if demo_mode else 'LIVE'}")
    
    # Initialize trader
    print("\n1️⃣ Initializing CapitalTrader...")
    try:
        trader = CapitalTrader(
            api_key=api_key,
            password=password,
            identifier=identifier,
            demo_mode=demo_mode
        )
        print("   ✅ Trader initialized")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Test account status
    print("\n2️⃣ Testing get_account_status()...")
    try:
        account = trader.get_account_status()
        print(f"   💰 Balance: {account.get('balance', 0):.2f} {account.get('currency', 'USD')}")
        print(f"   📊 Equity: {account.get('equity', 0):.2f}")
        print(f"   💵 Available: {account.get('available', 0):.2f}")
        print(f"   📈 PnL: {account.get('pnl', 0):.2f}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test positions
    print("\n3️⃣ Testing get_open_positions()...")
    try:
        positions = trader.get_open_positions()
        if positions:
            print(f"   📋 {len(positions)} open position(s):")
            for pos in positions:
                print(f"      - {pos['symbol']}: {pos['direction']} {pos['size']} @ {pos['entry_price']}")
        else:
            print("   📭 No open positions")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test fetch candles
    print("\n4️⃣ Testing fetch_candles(BTCUSD)...")
    try:
        candles = trader.fetch_candles("BTCUSD", "MINUTE_15", 5)
        if candles:
            print(f"   📊 Received {len(candles)} candles")
            last = candles[-1]
            print(f"   🕐 Last candle: {last['timestamp']}")
            print(f"   💵 OHLC: O={last['open']:.2f} H={last['high']:.2f} L={last['low']:.2f} C={last['close']:.2f}")
        else:
            print("   ⚠️ No candles received")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test market info
    print("\n5️⃣ Testing get_market_info(BTCUSD)...")
    try:
        market = trader.get_market_info("BTCUSD")
        if market:
            snapshot = market.get("snapshot", {})
            dealing = market.get("dealingRules", {})
            print(f"   💵 Bid: {snapshot.get('bid', 'N/A')}")
            print(f"   💵 Offer: {snapshot.get('offer', 'N/A')}")
            print(f"   📏 Min Size: {dealing.get('minDealSize', {}).get('value', 'N/A')}")
        else:
            print("   ⚠️ No market info")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test formatted status (for main.py compatibility)
    print("\n6️⃣ Testing get_account_status_formatted()...")
    try:
        formatted = trader.get_account_status_formatted()
        print(f"   💰 Balance USD: {formatted.get('balance_usd', 0):.2f}")
        print(f"   📋 Positions: {len(formatted.get('positions', []))}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS COMPLETED")
    print("=" * 60)
    return True

if __name__ == "__main__":
    test_connection()

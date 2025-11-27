import requests
import json
import time
import base64
from datetime import datetime
from typing import Dict, Any, List, Optional
import os

# Try to import crypto libraries for password encryption
try:
    from Crypto.PublicKey import RSA
    from Crypto.Cipher import PKCS1_v1_5
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False
    print("⚠️ pycryptodome not installed. Encrypted login will not be available.")


class CapitalTrader:
    """
    Capital.com API Trader - Gestisce autenticazione e trading su Capital.com
    
    Supporta:
    - Account Demo e Live
    - Apertura/Chiusura posizioni
    - Stop Loss / Take Profit / Trailing Stop
    - Candele storiche per analisi tecnica
    """
    
    def __init__(self, api_key: str, password: str, identifier: str, demo_mode: bool = True, account_id: str = None):
        self.api_key = api_key
        self.password = password
        self.identifier = identifier
        self.demo_mode = demo_mode
        self.account_id = account_id  # Opzionale: specifica quale conto usare
        
        if demo_mode:
            self.base_url = "https://demo-api-capital.backend-capital.com"
        else:
            self.base_url = "https://api-capital.backend-capital.com"
            
        self.session = requests.Session()
        self.cst = None
        self.x_security_token = None
        
        # Authenticate on init
        self._authenticate()
        
        # Switch to correct account if specified or use preferred
        self._select_account()

    def _authenticate(self):
        """Authenticate with Capital.com API"""
        url = f"{self.base_url}/api/v1/session"
        headers = {"X-CAP-API-KEY": self.api_key}
        payload = {
            "identifier": self.identifier,
            "password": self.password,
            "encryptedPassword": False
        }
        
        try:
            response = self.session.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                self._handle_auth_success(response)
            else:
                print(f"⚠️ Auth failed with status {response.status_code}: {response.text}")
                response.raise_for_status()
                
        except Exception as e:
            print(f"❌ Capital.com Authentication Error: {e}")
            raise

    def _handle_auth_success(self, response):
        self.cst = response.headers.get("CST")
        self.x_security_token = response.headers.get("X-SECURITY-TOKEN")
        
        if not self.cst or not self.x_security_token:
            raise ValueError("Authentication failed: Missing tokens in response headers")
            
        print("✅ Capital.com Authenticated Successfully")

    def _get_headers(self) -> Dict[str, str]:
        if not self.cst or not self.x_security_token:
            self._authenticate()
            
        return {
            "X-CAP-API-KEY": self.api_key,
            "CST": self.cst,
            "X-SECURITY-TOKEN": self.x_security_token,
            "Content-Type": "application/json"
        }

    def _select_account(self):
        """Seleziona il conto corretto (specificato o preferito)"""
        try:
            url = f"{self.base_url}/api/v1/accounts"
            response = self.session.get(url, headers=self._get_headers())
            response.raise_for_status()
            data = response.json()
            
            accounts = data.get("accounts", [])
            if not accounts:
                print("⚠️ Nessun conto trovato")
                return
            
            # Se è specificato un account_id, cercalo
            if self.account_id:
                target_account = next((a for a in accounts if a["accountId"] == self.account_id), None)
                if target_account:
                    self._switch_to_account(target_account)
                    return
                else:
                    print(f"⚠️ Account ID {self.account_id} non trovato, uso il preferito")
            
            # Altrimenti usa il conto preferito
            preferred_account = next((a for a in accounts if a.get("preferred", False)), None)
            if preferred_account:
                self._switch_to_account(preferred_account)
            else:
                # Fallback al primo conto
                self._switch_to_account(accounts[0])
                
        except Exception as e:
            print(f"⚠️ Errore selezione conto: {e}")

    def _switch_to_account(self, account: Dict):
        """Switch al conto specificato"""
        account_id = account.get("accountId")
        account_name = account.get("accountName", "Unknown")
        balance = account.get("balance", {}).get("balance", 0)
        
        try:
            url = f"{self.base_url}/api/v1/session"
            payload = {"accountId": account_id}
            response = self.session.put(url, headers=self._get_headers(), json=payload)
            
            if response.status_code == 200:
                # Aggiorna i token se presenti nella risposta
                if "CST" in response.headers:
                    self.cst = response.headers["CST"]
                if "X-SECURITY-TOKEN" in response.headers:
                    self.x_security_token = response.headers["X-SECURITY-TOKEN"]
                    
                print(f"✅ Conto selezionato: {account_name} (€{balance:,.2f})")
                self.active_account_id = account_id
                self.active_account_name = account_name
            elif response.status_code == 400 and "not-different" in response.text:
                # Conto già selezionato - OK
                print(f"✅ Conto già attivo: {account_name} (€{balance:,.2f})")
                self.active_account_id = account_id
                self.active_account_name = account_name
            else:
                print(f"⚠️ Switch account fallito: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Errore switch account: {e}")

    # ==========================================================================
    #                           ACCOUNT STATUS
    # ==========================================================================
    
    def get_account_status(self) -> Dict[str, Any]:
        """Get account balance and equity information for the active account"""
        url = f"{self.base_url}/api/v1/accounts"
        try:
            response = self.session.get(url, headers=self._get_headers())
            if response.status_code == 401:
                print("🔄 Session expired, re-authenticating...")
                self._authenticate()
                self._select_account()
                response = self.session.get(url, headers=self._get_headers())
                
            response.raise_for_status()
            data = response.json()
            accounts = data.get("accounts", [])
            
            # Trova il conto attivo
            account = None
            if hasattr(self, 'active_account_id') and self.active_account_id:
                account = next((a for a in accounts if a["accountId"] == self.active_account_id), None)
            
            # Fallback: conto preferito o primo
            if not account:
                account = next((a for a in accounts if a.get("preferred", False)), accounts[0] if accounts else None)
            
            if account:
                return {
                    "balance": account.get("balance", {}).get("balance", 0),
                    "equity": account.get("balance", {}).get("equity", 0),
                    "pnl": account.get("balance", {}).get("profitLoss", 0),
                    "available": account.get("balance", {}).get("available", 0),
                    "currency": account.get("currency", "EUR"),
                    "account_name": account.get("accountName", "Unknown")
                }
            return {}
        except Exception as e:
            print(f"❌ Error getting account status: {e}")
            return {}

    # ==========================================================================
    #                           POSITIONS
    # ==========================================================================
    
    def get_open_positions(self) -> List[Dict[str, Any]]:
        """Get all open positions"""
        url = f"{self.base_url}/api/v1/positions"
        try:
            response = self.session.get(url, headers=self._get_headers())
            if response.status_code == 401:
                self._authenticate()
                response = self.session.get(url, headers=self._get_headers())
            response.raise_for_status()
            data = response.json()
            positions = []
            for item in data.get("positions", []):
                pos = item.get("position", {})
                market = item.get("market", {})
                
                positions.append({
                    "dealId": pos.get("dealId"),
                    "dealReference": pos.get("dealReference"),
                    "symbol": market.get("epic"),
                    "direction": pos.get("direction"),
                    "size": pos.get("size"),
                    "entry_price": pos.get("level"),
                    "mark_price": market.get("bid") if pos.get("direction") == "SELL" else market.get("offer"),
                    "stopLevel": pos.get("stopLevel"),
                    "profitLevel": pos.get("profitLevel"),
                    "trailingStop": pos.get("trailingStop"),
                    "guaranteedStop": pos.get("guaranteedStop"),
                    "pnl": pos.get("upl"),
                    "created_at": pos.get("createdDate"),
                    "leverage": pos.get("leverage"),
                    "currency": pos.get("currency")
                })
            return positions
        except Exception as e:
            print(f"❌ Error getting open positions: {e}")
            return []

    # ==========================================================================
    #                           MARKET DATA
    # ==========================================================================
    
    def fetch_candles(self, epic: str, resolution: str = "MINUTE_15", limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch historical candles for technical analysis"""
        url = f"{self.base_url}/api/v1/prices/{epic}"
        params = {"resolution": resolution, "max": limit}
        try:
            response = self.session.get(url, headers=self._get_headers(), params=params)
            if response.status_code == 401:
                self._authenticate()
                response = self.session.get(url, headers=self._get_headers(), params=params)
            response.raise_for_status()
            data = response.json()
            candles = []
            for price in data.get("prices", []):
                candles.append({
                    "timestamp": price.get("snapshotTime"),
                    "open": price.get("openPrice", {}).get("bid"),
                    "high": price.get("highPrice", {}).get("bid"),
                    "low": price.get("lowPrice", {}).get("bid"),
                    "close": price.get("closePrice", {}).get("bid"),
                    "volume": price.get("lastTradedVolume", 0)
                })
            return candles
        except Exception as e:
            print(f"❌ Error fetching candles for {epic}: {e}")
            return []

    def get_deal_confirmation(self, deal_reference: str) -> Dict[str, Any]:
        """Get deal confirmation details including dealId from dealReference"""
        url = f"{self.base_url}/api/v1/confirms/{deal_reference}"
        try:
            response = self.session.get(url, headers=self._get_headers())
            if response.status_code == 401:
                self._authenticate()
                response = self.session.get(url, headers=self._get_headers())
            if response.status_code != 200:
                return {"status": "error", "message": response.text}
            return {"status": "ok", "data": response.json()}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def get_market_info(self, epic: str) -> Dict[str, Any]:
        """Get market details and dealing rules for a symbol"""
        url = f"{self.base_url}/api/v1/markets/{epic}"
        try:
            response = self.session.get(url, headers=self._get_headers())
            if response.status_code == 401:
                self._authenticate()
                response = self.session.get(url, headers=self._get_headers())
            if response.status_code != 200:
                return {}
            return response.json()
        except Exception as e:
            print(f"❌ Error getting market info for {epic}: {e}")
            return {}

    # ==========================================================================
    #                           TRADING
    # ==========================================================================
    
    def execute_order(self, epic: str, direction: str, size: float, 
                      stop_distance: float = None, profit_distance: float = None, 
                      trailing_stop: bool = False) -> Dict[str, Any]:
        """
        Execute a market order on Capital.com
        
        Args:
            epic: Instrument identifier (e.g., "BTCUSD", "ETHUSD", "SOLUSD")
            direction: "BUY" or "SELL"
            size: Position size
            stop_distance: Optional stop loss distance from entry
            profit_distance: Optional take profit distance from entry
            trailing_stop: Whether to use trailing stop (requires stop_distance)
        """
        url = f"{self.base_url}/api/v1/positions"
        
        payload = {
            "epic": epic, 
            "direction": direction.upper(),
            "size": size,
            "guaranteedStop": False
        }
        
        # Add Stop Loss if provided
        if stop_distance is not None and stop_distance > 0:
            payload["stopDistance"] = round(stop_distance, 5)
        
        # Add Take Profit if provided
        if profit_distance is not None and profit_distance > 0:
            payload["profitDistance"] = round(profit_distance, 5)
        
        # Add Trailing Stop if requested
        if trailing_stop and stop_distance is not None:
            payload["trailingStop"] = True
        
        try:
            print(f"🚀 Sending {direction} order for {size} {epic} to Capital.com...")
            response = self.session.post(url, headers=self._get_headers(), json=payload)
            if response.status_code == 401:
                self._authenticate()
                response = self.session.post(url, headers=self._get_headers(), json=payload)
            if response.status_code != 200:
                print(f"⚠️ Order failed: {response.text}")
                return {"status": "error", "message": response.text}
            
            data = response.json()
            deal_reference = data.get('dealReference')
            print(f"✅ Order executed: {deal_reference}")
            
            # Get dealId from confirmation
            deal_id = None
            if deal_reference:
                time.sleep(0.5)
                confirm = self.get_deal_confirmation(deal_reference)
                if confirm.get('status') == 'ok':
                    deal_id = confirm.get('data', {}).get('dealId')
            
            return {
                "status": "ok", 
                "dealReference": deal_reference,
                "dealId": deal_id,
                "data": data
            }
        except Exception as e:
            print(f"❌ Error executing order: {e}")
            return {"status": "error", "error": str(e)}

    def close_position(self, deal_id: str) -> Dict[str, Any]:
        """Close an open position by dealId"""
        url = f"{self.base_url}/api/v1/positions/{deal_id}"
        try:
            print(f"🗑️ Closing position {deal_id}...")
            response = self.session.delete(url, headers=self._get_headers())
            if response.status_code == 401:
                self._authenticate()
                response = self.session.delete(url, headers=self._get_headers())
            if response.status_code != 200:
                print(f"⚠️ Close failed: {response.text}")
                return {"status": "error", "message": response.text}
            data = response.json()
            print(f"✅ Position closed: {data.get('dealReference')}")
            return {"status": "ok", "dealReference": data.get("dealReference")}
        except Exception as e:
            print(f"❌ Error closing position: {e}")
            return {"status": "error", "error": str(e)}

    def update_position(self, deal_id: str, stop_level: float = None, stop_distance: float = None, 
                       profit_level: float = None, profit_distance: float = None, 
                       trailing_stop: bool = None) -> Dict[str, Any]:
        """Update stop/profit levels on an existing position"""
        url = f"{self.base_url}/api/v1/positions/{deal_id}"
        payload = {}
        
        if stop_level is not None:
            payload["stopLevel"] = stop_level
        if stop_distance is not None:
            payload["stopDistance"] = stop_distance
        if profit_level is not None:
            payload["profitLevel"] = profit_level
        if profit_distance is not None:
            payload["profitDistance"] = profit_distance
        if trailing_stop is not None:
            payload["trailingStop"] = trailing_stop
            
        try:
            response = self.session.put(url, headers=self._get_headers(), json=payload)
            if response.status_code == 401:
                self._authenticate()
                response = self.session.put(url, headers=self._get_headers(), json=payload)
            if response.status_code != 200:
                return {"status": "error", "message": response.text}
            data = response.json()
            return {"status": "ok", "dealReference": data.get("dealReference")}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    # ==========================================================================
    #                     HELPER FOR TRADING-AGENT INTEGRATION
    # ==========================================================================
    
    def execute_signal(self, order_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a trading signal from the AI agent.
        Compatible with the same interface as HyperLiquidTrader.
        
        Args:
            order_json: Dict with keys: operation, symbol, direction, 
                       target_portion_of_balance, leverage, reason
        """
        op = order_json.get("operation", "").lower()
        symbol = order_json.get("symbol", "")
        direction = order_json.get("direction", "").lower()
        portion = float(order_json.get("target_portion_of_balance", 0))
        leverage = int(order_json.get("leverage", 1))
        
        # Map symbol to Capital.com epic
        epic = self._map_symbol_to_epic(symbol)
        
        if op == "hold":
            print(f"[CapitalTrader] HOLD — nessuna azione per {symbol}.")
            return {"status": "hold", "message": "No action taken."}

        if op == "close":
            print(f"[CapitalTrader] Market CLOSE per {symbol}")
            positions = self.get_open_positions()
            position_to_close = None
            deal_id = None
            for p in positions:
                if p['symbol'] == epic:
                    deal_id = p['dealId']
                    position_to_close = p
                    break
            
            if deal_id:
                result = self.close_position(deal_id)
                if result.get('status') == 'ok':
                    print(f"[CapitalTrader] ✅ Posizione {symbol} chiusa con successo")
                    
                    # Registra il trade chiuso nello storico
                    if position_to_close:
                        try:
                            import db_utils
                            db_utils.log_trade_close_from_position(
                                position_to_close, 
                                close_reason=order_json.get("reason", "AI decision")
                            )
                            print(f"[CapitalTrader] 📊 Trade registrato nello storico")
                        except Exception as e:
                            print(f"[CapitalTrader] ⚠️ Errore registrazione storico: {e}")
                    
                    # Sincronizza real_positions con Capital.com
                    try:
                        import db_utils
                        updated_positions = self.get_open_positions()
                        db_utils.sync_real_positions(updated_positions)
                        print(f"[CapitalTrader] 🔄 real_positions sincronizzato")
                    except Exception as e:
                        print(f"[CapitalTrader] ⚠️ Errore sync real_positions: {e}")
                else:
                    print(f"[CapitalTrader] ⚠️ Chiusura fallita: {result}")
                return result
            else:
                print(f"[CapitalTrader] ⚠️ Nessuna posizione aperta per {symbol}")
                return {"status": "skipped", "message": "No position to close"}

        if op == "open":
            # Get account balance
            account = self.get_account_status()
            balance = account.get("balance", 0)
            
            if balance <= 0:
                return {"status": "error", "message": "No balance available"}
            
            # Get market info for price
            market_info = self.get_market_info(epic)
            snapshot = market_info.get("snapshot", {})
            current_price = snapshot.get("offer") if direction == "long" else snapshot.get("bid")
            
            if not current_price:
                return {"status": "error", "message": "Could not get current price"}
            
            # Calculate size based on portion and leverage
            # For crypto: size is in units of the asset
            notional = balance * portion * leverage
            size = notional / current_price
            
            # Round size according to dealing rules
            dealing_rules = market_info.get("dealingRules", {})
            min_size = dealing_rules.get("minDealSize", {}).get("value", 0.0001)
            
            # Ensure size meets minimum
            if size < min_size:
                size = min_size
            
            # Round to appropriate decimals for crypto
            size = round(size, 4)  # 4 decimals for crypto
            
            cap_direction = "BUY" if direction == "long" else "SELL"
            
            print(f"\n[CapitalTrader] Market {cap_direction} {size} {epic}")
            print(f"  💰 Prezzo: ${current_price}")
            print(f"  📊 Notional: ${notional:.2f}")
            print(f"  🎯 Leverage: {leverage}x (via position size)")
            
            result = self.execute_order(epic, cap_direction, size)
            
            # Sincronizza real_positions dopo apertura
            if result.get('status') == 'ok':
                try:
                    import db_utils
                    # Attendi un attimo che Capital.com aggiorni lo stato
                    import time
                    time.sleep(0.5)
                    updated_positions = self.get_open_positions()
                    db_utils.sync_real_positions(updated_positions)
                    print(f"[CapitalTrader] 🔄 real_positions sincronizzato ({len(updated_positions)} posizioni)")
                except Exception as e:
                    print(f"[CapitalTrader] ⚠️ Errore sync real_positions: {e}")
            
            return result

        return {"status": "error", "message": f"Unknown operation: {op}"}

    def _map_symbol_to_epic(self, symbol: str) -> str:
        """Map common symbol names to Capital.com EPICs"""
        mapping = {
            "BTC": "BTCUSD",
            "BTCUSD": "BTCUSD",
            "ETH": "ETHUSD",
            "ETHUSD": "ETHUSD",
            "SOL": "SOLUSD",
            "SOLUSD": "SOLUSD",
        }
        return mapping.get(symbol.upper(), symbol.upper())

    def get_account_status_formatted(self) -> Dict[str, Any]:
        """
        Get account status in the same format as HyperLiquidTrader
        for compatibility with main.py
        """
        account = self.get_account_status()
        positions = self.get_open_positions()
        
        formatted_positions = []
        for pos in positions:
            # Reverse map epic to symbol
            epic = pos.get('epic', pos.get('symbol', ''))
            symbol = epic.replace("USD", "") if epic.endswith("USD") else epic
            
            formatted_positions.append({
                "deal_id": pos.get('dealId'),  # Capital.com deal ID
                "symbol": symbol,
                "epic": epic,
                "side": "long" if pos.get('direction') == "BUY" else "short",
                "direction": pos.get('direction', 'BUY'),
                "size": pos.get('size', 0),
                "entry_price": pos.get('entry_price') or pos.get('openLevel'),
                "mark_price": pos.get('mark_price') or pos.get('currentLevel'),
                "openLevel": pos.get('openLevel'),
                "currentLevel": pos.get('currentLevel'),
                "pnl_usd": pos.get('pnl') or pos.get('profit') or 0,
                "profit": pos.get('profit') or pos.get('pnl') or 0,
                "stopLevel": pos.get('stopLevel'),
                "limitLevel": pos.get('limitLevel'),
                "leverage": "N/A (CFD)"
            })
        
        return {
            "balance_usd": account.get("balance", 0),
            "equity": account.get("equity", 0),
            "available": account.get("available", 0),
            "pnl": account.get("pnl", 0),
            "currency": account.get("currency", "EUR"),
            "account_name": account.get("account_name", "Unknown"),
            "positions": formatted_positions,
            "open_positions": formatted_positions,  # Keep both for compatibility
        }

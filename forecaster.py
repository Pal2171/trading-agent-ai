import pandas as pd
from datetime import datetime, timezone, timedelta
from prophet import Prophet
import warnings
warnings.filterwarnings('ignore')


class CryptoForecaster:
    """Forecaster che usa Capital.com per i dati di prezzo"""
    
    def __init__(self, capital_client=None):
        self.capital_client = capital_client
        self.last_prices = {}

    def _fetch_candles_capital(self, epic: str, resolution: str, limit: int) -> pd.DataFrame:
        """Fetch candles da Capital.com"""
        if not self.capital_client:
            raise RuntimeError("Capital.com client not provided")
        
        candles = self.capital_client.fetch_candles(epic, resolution=resolution, limit=limit)
        
        if not candles:
            raise RuntimeError(f"No candles for {epic} {resolution}")
        
        df = pd.DataFrame(candles)
        df["ds"] = pd.to_datetime(df["timestamp"])
        df["y"] = df["close"].astype(float)
        df = df[["ds", "y"]].sort_values("ds").reset_index(drop=True)
        return df

    def _map_ticker_to_epic(self, ticker: str) -> str:
        """Mappa ticker a Capital.com EPIC"""
        mapping = {
            "BTC": "BTCUSD",
            "ETH": "ETHUSD", 
            "SOL": "SOLUSD",
            "BTCUSD": "BTCUSD",
            "ETHUSD": "ETHUSD",
            "SOLUSD": "SOLUSD",
        }
        return mapping.get(ticker.upper(), ticker.upper())

    def _map_interval_to_resolution(self, interval: str) -> str:
        """Mappa intervallo a Capital.com resolution"""
        mapping = {
            "15m": "MINUTE_15",
            "1h": "HOUR",
        }
        return mapping.get(interval, "MINUTE_15")

    def forecast(self, ticker: str, interval: str) -> tuple:
        """Genera forecast per un ticker e intervallo"""
        epic = self._map_ticker_to_epic(ticker)
        resolution = self._map_interval_to_resolution(interval)
        
        limit = 300 if interval == "15m" else 500
        freq = "15min" if interval == "15m" else "H"
        
        df = self._fetch_candles_capital(epic, resolution, limit)
        
        # Memorizza l'ultimo prezzo
        last_price = df["y"].iloc[-1]

        model = Prophet(daily_seasonality=True, weekly_seasonality=True)
        model.fit(df)

        future = model.make_future_dataframe(periods=1, freq=freq)
        forecast = model.predict(future)

        return forecast.tail(1)[["ds", "yhat", "yhat_lower", "yhat_upper"]], last_price

    def forecast_many(self, tickers: list, intervals=("15m", "1h")):
        """Genera forecasts per multipli ticker e intervalli"""
        results = []
        for ticker in tickers:
            for interval in intervals:
                try:
                    forecast_data, last_price = self.forecast(ticker, interval)
                    fc = forecast_data.iloc[0]
                    
                    variazione_pct = ((fc["yhat"] - last_price) / last_price) * 100
                    timeframe = "Prossimi 15 Minuti" if interval == "15m" else "Prossima Ora"
                    
                    results.append({
                        "Ticker": ticker,
                        "Timeframe": timeframe,
                        "Ultimo Prezzo": round(last_price, 2),
                        "Previsione": round(fc["yhat"], 2),
                        "Limite Inferiore": round(fc["yhat_lower"], 2),
                        "Limite Superiore": round(fc["yhat_upper"], 2),
                        "Variazione %": round(variazione_pct, 2),
                        "Timestamp Previsione": fc["ds"]
                    })
                except Exception as e:
                    results.append({
                        "Ticker": ticker,
                        "Timeframe": "Prossimi 15 Minuti" if interval == "15m" else "Prossima Ora",
                        "Ultimo Prezzo": None,
                        "Previsione": None,
                        "Limite Inferiore": None,
                        "Limite Superiore": None,
                        "Variazione %": None,
                        "Timestamp Previsione": None,
                        "error": str(e)
                    })
        return results


def get_crypto_forecasts(tickers=['BTC', 'ETH', 'SOL'], testnet=True, capital_client=None):
    """
    Funzione principale per generare forecasts.
    Richiede capital_client per funzionare.
    """
    if capital_client is None:
        return "Forecasts non disponibili (capital_client non fornito)", "[]"
    
    try:
        forecaster = CryptoForecaster(capital_client=capital_client)
        results = forecaster.forecast_many(tickers)
        
        df = pd.DataFrame(results)
        if 'error' in df.columns:
            df = df.drop('error', axis=1)
            
        return df.to_string(index=False), df.to_json(orient='records')
    except Exception as e:
        return f"Errore forecasts: {e}", "[]"
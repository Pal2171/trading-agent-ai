import pandas as pd
import ta
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Tuple, Optional, Any


# Mapping for Capital.com intervals
CAPITAL_INTERVAL_MAP = {
    "1m": "MINUTE",
    "5m": "MINUTE_5",
    "15m": "MINUTE_15",
    "1h": "HOUR",
    "4h": "HOUR_4",
    "1d": "DAY",
}

# Mapping ticker to Capital.com EPIC
TICKER_TO_EPIC = {
    "BTC": "BTCUSD",
    "ETH": "ETHUSD", 
    "SOL": "SOLUSD",
}


class CryptoTechnicalAnalysis:
    """
    Analisi tecnica usando Capital.com API.
    Tutti gli indicatori principali sono centrati sul timeframe 15 minuti.
    """

    def __init__(self, capital_client: Any):
        if capital_client is None:
            raise ValueError("capital_client è obbligatorio")
        self.capital_client = capital_client

    # ==============================
    #       FETCH OHLCV
    # ==============================

    def get_orderbook_volume(self, ticker: str) -> str:
        """Capital.com non fornisce orderbook, restituiamo N/A"""
        return "N/A (Capital.com)"

    def fetch_ohlcv(self, coin: str, interval: str, limit: int = 500) -> pd.DataFrame:
        """Recupera i dati OHLCV da Capital.com."""
        epic = TICKER_TO_EPIC.get(coin.upper(), coin.upper() + "USD")
        resolution = CAPITAL_INTERVAL_MAP.get(interval, "MINUTE_15")
        
        candles = self.capital_client.fetch_candles(epic, resolution, limit)
        
        if not candles:
            raise RuntimeError(f"Nessuna candela ricevuta da Capital.com per {epic}")
        
        df = pd.DataFrame(candles)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        if df["timestamp"].dt.tz is None:
            df["timestamp"] = df["timestamp"].dt.tz_localize('UTC')
        
        for col in ["open", "high", "low", "close", "volume"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        df = df.sort_values("timestamp").reset_index(drop=True)
        return df

    # ==============================
    #       INDICATORI TECNICI
    # ==============================
    def calculate_ema(self, data: pd.Series, period: int) -> pd.Series:
        return ta.trend.EMAIndicator(data, window=period).ema_indicator()

    def calculate_macd(self, data: pd.Series) -> Tuple[pd.Series, pd.Series, pd.Series]:
        macd = ta.trend.MACD(data)
        return macd.macd(), macd.macd_signal(), macd.macd_diff()

    def calculate_rsi(self, data: pd.Series, period: int) -> pd.Series:
        return ta.momentum.RSIIndicator(data, window=period).rsi()

    def calculate_atr(
        self, high: pd.Series, low: pd.Series, close: pd.Series, period: int
    ) -> pd.Series:
        return ta.volatility.AverageTrueRange(
            high, low, close, window=period
        ).average_true_range()

    def calculate_pivot_points(
        self, high: float, low: float, close: float
    ) -> Dict[str, float]:
        pp = (high + low + close) / 3.0
        s1 = (2 * pp) - high
        s2 = pp - (high - low)
        r1 = (2 * pp) - low
        r2 = pp + (high - low)
        return {"pp": pp, "s1": s1, "s2": s2, "r1": r1, "r2": r2}

    # ==============================
    #   FUNDING / OI (placeholder)
    # ==============================
    def get_funding_rate(self, coin: str) -> float:
        """
        Per ora ritorniamo 0.0 per evitare problemi di compatibilità se
        la tua versione dell'SDK non espone funding_history.
        """
        return 0.0

    def get_open_interest(self, coin: str) -> Dict[str, float]:
        """
        Hyperliquid non espone un semplice 'open interest globale' via SDK.
        Placeholder che ritorna 0.0.
        """
        return {"latest": 0.0, "average": 0.0}

    # ==============================
    #   ANALISI COMPLETA A 15m
    # ==============================
    def get_complete_analysis(self, ticker: str) -> Dict:
        coin = ticker.upper()

        # 1) DATI 15 MINUTI (intraday principale)
        df_15m = self.fetch_ohlcv(coin, "15m", limit=200)

        df_15m["ema_20"] = self.calculate_ema(df_15m["close"], 20)
        macd_line, signal_line, macd_diff = self.calculate_macd(df_15m["close"])
        df_15m["macd"] = macd_diff
        df_15m["rsi_7"] = self.calculate_rsi(df_15m["close"], 7)
        df_15m["rsi_14"] = self.calculate_rsi(df_15m["close"], 14)

        last_10_15m = df_15m.tail(10)

        # 2) CONTESTO "longer term" sempre a 15m ma su finestra più lunga
        longer_term = df_15m.tail(50).copy()
        longer_term["ema_20"] = self.calculate_ema(longer_term["close"], 20)
        longer_term["ema_50"] = self.calculate_ema(longer_term["close"], 50)
        longer_term["atr_3"] = self.calculate_atr(
            longer_term["high"], longer_term["low"], longer_term["close"], 3
        )
        longer_term["atr_14"] = self.calculate_atr(
            longer_term["high"], longer_term["low"], longer_term["close"], 14
        )
        macd_15m_long, _, macd_diff_15m_long = self.calculate_macd(
            longer_term["close"]
        )
        longer_term["macd"] = macd_diff_15m_long
        longer_term["rsi_14"] = self.calculate_rsi(longer_term["close"], 14)

        avg_volume = longer_term["volume"].tail(20).mean()
        last_10_longer = longer_term.tail(10)

        # 3) PIVOT POINTS daily
        df_daily = self.fetch_ohlcv(coin, "1d", limit=2)
        if len(df_daily) >= 2:
            prev_day = df_daily.iloc[-2]
            pivot_points = self.calculate_pivot_points(
                prev_day["high"], prev_day["low"], prev_day["close"]
            )
        else:
            last = df_15m.iloc[-1]
            pivot_points = self.calculate_pivot_points(
                last["high"], last["low"], last["close"]
            )

        oi_data = self.get_open_interest(coin)
        funding_rate = self.get_funding_rate(coin)

        current_15m = df_15m.iloc[-1]
        current_longer = longer_term.iloc[-1]

        result = {
            "ticker": ticker,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            
            "current": {
                "price": current_15m["close"],
                "ema20": current_15m["ema_20"],
                "macd": current_15m["macd"],
                "rsi_7": current_15m["rsi_7"],
            },
            "volume": self.get_orderbook_volume(ticker),
            "pivot_points": pivot_points,

            "derivatives": {
                "open_interest_latest": oi_data["latest"],
                "open_interest_average": oi_data["average"],
                "funding_rate": funding_rate,
            },

            "intraday": {
                "mid_prices": last_10_15m["close"].tolist(),
                "ema_20": last_10_15m["ema_20"].tolist(),
                "macd": last_10_15m["macd"].tolist(),
                "rsi_7": last_10_15m["rsi_7"].tolist(),
                "rsi_14": last_10_15m["rsi_14"].tolist(),
            },

            "longer_term_15m": {
                "ema_20_current": current_longer["ema_20"],
                "ema_50_current": current_longer["ema_50"],
                "atr_3_current": current_longer["atr_3"],
                "atr_14_current": current_longer["atr_14"],
                "volume_current": current_longer["volume"],
                "volume_average": avg_volume,
                "macd_series": last_10_longer["macd"].tolist(),
                "rsi_14_series": last_10_longer["rsi_14"].tolist(),
            },
        }
        return result

    def format_output(self, data: Dict) -> str:
        output = f"\n<{data['ticker']}_data>\n"
        output += f"Timestamp: {data['timestamp']} (UTC) (Capital.com, 15m)\n"
        output += f"\n"

        curr = data["current"]
        output += (
            f"current_price = {curr['price']:.1f}, "
            f"current_ema20 = {curr['ema20']:.3f}, "
            f"current_macd = {curr['macd']:.3f}, "
            f"current_rsi (7 period) = {curr['rsi_7']:.3f}\n\n"
        )
        output += f"Volume: {data['volume']}\n\n"

        pivot = data["pivot_points"]
        output += "Pivot Points (based on previous day):\n"
        output += (
            f"R2 = {pivot['r2']:.2f}, R1 = {pivot['r1']:.2f}, "
            f"PP = {pivot['pp']:.2f}, "
            f"S1 = {pivot['s1']:.2f}, S2 = {pivot['s2']:.2f}\n\n"
        )

        intra = data["intraday"]
        output += "Intraday series (15m, oldest → latest):\n"
        output += (
            f"Mid prices: {[round(x, 1) for x in intra['mid_prices']]}\n"
            f"EMA indicators (20-period): {[round(x, 3) for x in intra['ema_20']]}\n"
            f"MACD indicators: {[round(x, 3) for x in intra['macd']]}\n"
            f"RSI indicators (7-Period): {[round(x, 3) for x in intra['rsi_7']]}\n"
            f"RSI indicators (14-Period): {[round(x, 3) for x in intra['rsi_14']]}\n\n"
        )

        lt = data["longer_term_15m"]
        output += "Longer-term context (still 15-minute timeframe, wider window):\n"
        output += (
            f"20-Period EMA: {lt['ema_20_current']:.3f} vs. "
            f"50-Period EMA: {lt['ema_50_current']:.3f}\n"
            f"3-Period ATR: {lt['atr_3_current']:.3f} vs. "
            f"14-Period ATR: {lt['atr_14_current']:.3f}\n"
            f"Current Volume: {lt['volume_current']:.3f} vs. "
            f"Average Volume: {lt['volume_average']:.3f}\n"
            f"MACD indicators: {[round(x, 3) for x in lt['macd_series']]}\n"
            f"RSI indicators (14-Period): {[round(x, 3) for x in lt['rsi_14_series']]}\n"
        )
        output += f"</{data['ticker']}_data>\n"
        return output


def analyze_multiple_tickers(tickers: List[str], capital_client: Any) -> Tuple[str, List]:
    """
    Analizza più ticker e restituisce output formattato + dati JSON.
    
    Args:
        tickers: Lista di ticker (es. ['BTC', 'ETH', 'SOL'])
        capital_client: Istanza CapitalTrader (obbligatorio)
    """
    if capital_client is None:
        raise ValueError("capital_client è obbligatorio per analyze_multiple_tickers")
    
    analyzer = CryptoTechnicalAnalysis(capital_client)
    full_output = ""
    datas = []
    
    for ticker in tickers:
        try:
            data = analyzer.get_complete_analysis(ticker)
            datas.append(data)
            full_output += analyzer.format_output(data)
        except Exception as e:
            print(f"Errore durante l'analisi di {ticker}: {e}")
    
    return full_output, datas


# if __name__ == "__main__":
#     tickers = ["BTC", "ETH", "BNB"]
#     result = analyze_multiple_tickers(tickers, testnet=True)
#     print(result)

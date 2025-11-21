import pandas as pd
import ta
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Tuple

from hyperliquid.info import Info
from hyperliquid.utils import constants


INTERVAL_TO_MS = {
    "1m": 60_000,
    "5m": 5 * 60_000,
    "15m": 15 * 60_000,
    "30m": 30 * 60_000,
    "1h": 60 * 60_000,
    "4h": 4 * 60 * 60_000,
    "1d": 24 * 60 * 60_000,
}


class CryptoTechnicalAnalysisHL:
    """
    Analisi tecnica usando l'API Info di Hyperliquid.
    Tutti gli indicatori principali sono centrati sul timeframe 15 minuti.
    """

    def __init__(self, testnet: bool = True):
        base_url = constants.TESTNET_API_URL if testnet else constants.MAINNET_API_URL
        self.info = Info(base_url, skip_ws=True)

    # ==============================
    #       FETCH OHLCV (HL)
    # ==============================

    def get_orderbook_volume(self, ticker: str) -> str:
        """
        Restituisce una stringa con i volumi totali di bid e ask per un ticker (es. 'btc-usd').
        Usa Info.l2_snapshot() dal wrapper ufficiale Hyperliquid.
        """
        coin = ticker.split('-')[0].upper()  # es. "BTC" da "btc-usd"

        try:
            orderbook = self.info.l2_snapshot(coin)
        except Exception as e:
            return f"Errore recuperando orderbook: {e}"

        if not orderbook or "levels" not in orderbook:
            return f"Nessun dato disponibile per {coin}"

        bids = orderbook["levels"][0]
        asks = orderbook["levels"][1]

        bid_volume = sum(float(level["sz"]) for level in bids)
        ask_volume = sum(float(level["sz"]) for level in asks)

        return f"Bid Vol: {bid_volume}, Ask Vol: {ask_volume}"

    def fetch_ohlcv(self, coin: str, interval: str, limit: int = 500) -> pd.DataFrame:
        """
        Recupera i dati OHLCV da Hyperliquid tramite Info.candles_snapshot.

        Args:
            coin: asset Hyperliquid (es. 'BTC', 'ETH')
            interval: es. '15m', '1d'
            limit: numero massimo di candele circa (usato per la finestra temporale)

        Returns:
            DataFrame con colonne: timestamp, open, high, low, close, volume
        """
        if interval not in INTERVAL_TO_MS:
            raise ValueError(f"Interval '{interval}' non supportato in INTERVAL_TO_MS")

        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        step_ms = INTERVAL_TO_MS[interval]
        start_ms = now_ms - limit * step_ms

        # ⚠️ Metodo corretto: candles_snapshot (non candle_snapshot)
        ohlcv_data = self.info.candles_snapshot(
            name=coin,
            interval=interval,
            startTime=start_ms,
            endTime=now_ms,
        )

        if not ohlcv_data:
            raise RuntimeError(f"Nessuna candela ricevuta per {coin} ({interval})")

        df = pd.DataFrame(ohlcv_data)

        # df ha colonne tipo: t, T, o, h, l, c, v, n, s, i
        df["timestamp"] = pd.to_datetime(df["t"], unit="ms", utc=True)

        # tieni solo quello che ci serve
        df = df[["timestamp", "o", "h", "l", "c", "v"]].copy()
        df.rename(
            columns={
                "o": "open",
                "h": "high",
                "l": "low",
                "c": "close",
                "v": "volume",
            },
            inplace=True,
        )

        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = df[col].astype(float)

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

    def calculate_supertrend(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 10, multiplier: float = 3.0) -> pd.DataFrame:
        atr = ta.volatility.AverageTrueRange(high, low, close, window=period).average_true_range()
        
        hl2 = (high + low) / 2
        final_upperband = hl2 + (multiplier * atr)
        final_lowerband = hl2 - (multiplier * atr)
        
        supertrend = [True] * len(close)
        
        for i in range(1, len(close)):
            curr_close = close.iloc[i]
            prev_close = close.iloc[i-1]
            
            if final_upperband.iloc[i] < final_upperband.iloc[i-1] or prev_close > final_upperband.iloc[i-1]:
                final_upperband.iloc[i] = final_upperband.iloc[i]
            else:
                final_upperband.iloc[i] = final_upperband.iloc[i-1]
                
            if final_lowerband.iloc[i] > final_lowerband.iloc[i-1] or prev_close < final_lowerband.iloc[i-1]:
                final_lowerband.iloc[i] = final_lowerband.iloc[i]
            else:
                final_lowerband.iloc[i] = final_lowerband.iloc[i-1]
                
            if supertrend[i-1] == True:
                if curr_close <= final_lowerband.iloc[i]:
                    supertrend[i] = False
                else:
                    supertrend[i] = True
            else:
                if curr_close >= final_upperband.iloc[i]:
                    supertrend[i] = True
                else:
                    supertrend[i] = False
                    
        return pd.DataFrame({
            'Supertrend': supertrend,
            'Final Lowerband': final_lowerband,
            'Final Upperband': final_upperband
        })

    def calculate_adx(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        return ta.trend.ADXIndicator(high, low, close, window=period).adx()

    def detect_candlestick_patterns(self, df: pd.DataFrame, lookback: int = 10) -> Dict[str, any]:
        """
        Rileva i principali pattern candlestick giapponesi sulle ultime candele.
        Restituisce un dict con i pattern rilevati e la loro interpretazione.
        """
        if len(df) < lookback:
            return {"patterns": [], "interpretation": "Dati insufficienti"}
        
        recent = df.tail(lookback).copy()
        patterns_found = []
        
        # Ultimi 3 candelabri per l'analisi
        if len(recent) >= 3:
            c0 = recent.iloc[-3]  # 2 candele fa
            c1 = recent.iloc[-2]  # candela precedente
            c2 = recent.iloc[-1]  # candela corrente
            
            # Calcola body e shadow per ogni candela
            def candle_info(candle):
                body = abs(candle['close'] - candle['open'])
                total_range = candle['high'] - candle['low']
                upper_shadow = candle['high'] - max(candle['open'], candle['close'])
                lower_shadow = min(candle['open'], candle['close']) - candle['low']
                is_bullish = candle['close'] > candle['open']
                return {
                    'body': body,
                    'range': total_range,
                    'upper_shadow': upper_shadow,
                    'lower_shadow': lower_shadow,
                    'is_bullish': is_bullish
                }
            
            info0 = candle_info(c0)
            info1 = candle_info(c1)
            info2 = candle_info(c2)
            
            # DOJI - corpo molto piccolo rispetto al range
            if info2['range'] > 0 and info2['body'] / info2['range'] < 0.1:
                patterns_found.append({
                    'name': 'Doji',
                    'type': 'reversal',
                    'signal': 'neutral',
                    'description': 'Indecisione del mercato, possibile inversione'
                })
            
            # HAMMER - corpo piccolo in alto, lunga shadow inferiore
            if (info2['lower_shadow'] > info2['body'] * 2 and 
                info2['upper_shadow'] < info2['body'] * 0.3):
                patterns_found.append({
                    'name': 'Hammer',
                    'type': 'reversal',
                    'signal': 'bullish',
                    'description': 'Possibile inversione rialzista, pressione acquisto'
                })
            
            # SHOOTING STAR - corpo piccolo in basso, lunga shadow superiore
            if (info2['upper_shadow'] > info2['body'] * 2 and 
                info2['lower_shadow'] < info2['body'] * 0.3):
                patterns_found.append({
                    'name': 'Shooting Star',
                    'type': 'reversal',
                    'signal': 'bearish',
                    'description': 'Possibile inversione ribassista, pressione vendita'
                })
            
            # ENGULFING BULLISH - candela rialzista che ingloba la precedente ribassista
            if (not info1['is_bullish'] and info2['is_bullish'] and
                c2['open'] < c1['close'] and c2['close'] > c1['open']):
                patterns_found.append({
                    'name': 'Bullish Engulfing',
                    'type': 'reversal',
                    'signal': 'bullish',
                    'description': 'Forte segnale rialzista, buyers prendono controllo'
                })
            
            # ENGULFING BEARISH - candela ribassista che ingloba la precedente rialzista
            if (info1['is_bullish'] and not info2['is_bullish'] and
                c2['open'] > c1['close'] and c2['close'] < c1['open']):
                patterns_found.append({
                    'name': 'Bearish Engulfing',
                    'type': 'reversal',
                    'signal': 'bearish',
                    'description': 'Forte segnale ribassista, sellers prendono controllo'
                })
            
            # MORNING STAR - pattern a 3 candele (ribassista + piccola + rialzista)
            if len(recent) >= 3:
                if (not info0['is_bullish'] and 
                    info1['body'] < info0['body'] * 0.5 and
                    info2['is_bullish'] and
                    c2['close'] > (c0['open'] + c0['close']) / 2):
                    patterns_found.append({
                        'name': 'Morning Star',
                        'type': 'reversal',
                        'signal': 'bullish',
                        'description': 'Pattern di inversione rialzista a 3 candele'
                    })
            
            # EVENING STAR - pattern a 3 candele (rialzista + piccola + ribassista)
                if (info0['is_bullish'] and 
                    info1['body'] < info0['body'] * 0.5 and
                    not info2['is_bullish'] and
                    c2['close'] < (c0['open'] + c0['close']) / 2):
                    patterns_found.append({
                        'name': 'Evening Star',
                        'type': 'reversal',
                        'signal': 'bearish',
                        'description': 'Pattern di inversione ribassista a 3 candele'
                    })
        
        # Interpretazione generale
        if not patterns_found:
            interpretation = "Nessun pattern significativo rilevato"
        else:
            bullish_count = sum(1 for p in patterns_found if p['signal'] == 'bullish')
            bearish_count = sum(1 for p in patterns_found if p['signal'] == 'bearish')
            
            if bullish_count > bearish_count:
                interpretation = f"BULLISH - {bullish_count} pattern rialzisti rilevati"
            elif bearish_count > bullish_count:
                interpretation = f"BEARISH - {bearish_count} pattern ribassisti rilevati"
            else:
                interpretation = "MIXED - Segnali contrastanti"
        
        return {
            'patterns': patterns_found,
            'interpretation': interpretation,
            'total_patterns': len(patterns_found)
        }

    def get_funding_rate(self, coin: str) -> float:
        return 0.0

    def get_open_interest(self, coin: str) -> Dict[str, float]:
        return {"latest": 0.0, "average": 0.0}

    def get_complete_analysis(self, ticker: str) -> Dict:
        coin = ticker.upper()

        df_15m = self.fetch_ohlcv(coin, "15m", limit=200)

        df_15m["ema_9"] = self.calculate_ema(df_15m["close"], 9)
        df_15m["ema_21"] = self.calculate_ema(df_15m["close"], 21)
        df_15m["ema_20"] = self.calculate_ema(df_15m["close"], 20)
        
        macd_line, signal_line, macd_diff = self.calculate_macd(df_15m["close"])
        df_15m["macd"] = macd_diff
        df_15m["rsi_7"] = self.calculate_rsi(df_15m["close"], 7)
        df_15m["rsi_14"] = self.calculate_rsi(df_15m["close"], 14)
        
        df_15m["adx"] = self.calculate_adx(df_15m["high"], df_15m["low"], df_15m["close"], 14)
        
        st_data = self.calculate_supertrend(df_15m["high"], df_15m["low"], df_15m["close"])
        df_15m["supertrend"] = st_data["Supertrend"]

        last_10_15m = df_15m.tail(10)

        longer_term = df_15m.tail(50).copy()
        longer_term["ema_20"] = self.calculate_ema(longer_term["close"], 20)
        longer_term["ema_50"] = self.calculate_ema(longer_term["close"], 50)
        longer_term["atr_3"] = self.calculate_atr(longer_term["high"], longer_term["low"], longer_term["close"], 3)
        longer_term["atr_14"] = self.calculate_atr(longer_term["high"], longer_term["low"], longer_term["close"], 14)
        macd_15m_long, _, macd_diff_15m_long = self.calculate_macd(longer_term["close"])
        longer_term["macd"] = macd_diff_15m_long
        longer_term["rsi_14"] = self.calculate_rsi(longer_term["close"], 14)

        avg_volume = longer_term["volume"].tail(20).mean()
        last_10_longer = longer_term.tail(10)

        # Analisi candlestick patterns
        candlestick_analysis = self.detect_candlestick_patterns(df_15m, lookback=10)

        oi_data = self.get_open_interest(coin)
        funding_rate = self.get_funding_rate(coin)

        current_15m = df_15m.iloc[-1]
        current_longer = longer_term.iloc[-1]

        result = {
            "ticker": ticker,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            
            "current": {
                "price": current_15m["close"],
                "ema_9": current_15m["ema_9"],
                "ema_21": current_15m["ema_21"],
                "supertrend": "BULLISH" if current_15m["supertrend"] else "BEARISH",
                "adx": current_15m["adx"],
                "ema20": current_15m["ema_20"],
                "macd": current_15m["macd"],
                "rsi_7": current_15m["rsi_7"],
                "rsi_14": current_15m["rsi_14"],
            },
            "volume": self.get_orderbook_volume(ticker),
            "candlestick_patterns": candlestick_analysis,

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
        output += f"Timestamp: {data['timestamp']} (UTC) (Hyperliquid, 15m)\n"
        output += f"\n"

        curr = data["current"]
        output += (
            f"current_price = {curr['price']:.1f}\n"
            f"Supertrend = {curr['supertrend']}\n"
            f"ADX (Trend Strength) = {curr['adx']:.1f}\n"
            f"EMA 9 = {curr['ema_9']:.2f}, EMA 21 = {curr['ema_21']:.2f}\n"
            f"RSI (14) = {curr['rsi_14']:.1f}\n"
            f"current_macd = {curr['macd']:.3f}\n\n"
        )
        output += f"Volume: {data['volume']}\n\n"

        # Candlestick Patterns
        candles = data["candlestick_patterns"]
        output += f"Candlestick Analysis: {candles['interpretation']}\n"
        if candles['patterns']:
            output += "Patterns rilevati:\n"
            for pattern in candles['patterns']:
                output += f"  • {pattern['name']} ({pattern['signal'].upper()}): {pattern['description']}\n"
        output += "\n"

        deriv = data["derivatives"]
        output += (
            f"In addition, here is the latest {data['ticker']} funding data on Hyperliquid:\n"
        )
        output += (
            f"Open Interest (placeholder): Latest: {deriv['open_interest_latest']:.2f} "
            f"Average: {deriv['open_interest_average']:.2f}\n"
        )
        output += f"Funding Rate: {deriv['funding_rate']:.2e}\n\n"

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
        output += f"<{data['ticker']}_data>\n"
        return output


def analyze_multiple_tickers(tickers: List[str], testnet: bool = True) -> str:
    analyzer = CryptoTechnicalAnalysisHL(testnet=testnet)
    full_output = ""
    datas = []
    data = None
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

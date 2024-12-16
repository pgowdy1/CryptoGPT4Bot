# technical_analysis.py
import pandas as pd
import ta
from ta.trend import MACD, SMAIndicator, EMAIndicator
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volatility import BollingerBands
from ta.volume import VolumeWeightedAveragePrice

class TechnicalAnalysis:
    def __init__(self, exchange):
        self.exchange = exchange

    def calculate_indicators(self, symbol):
        try:
            # Fetch historical data
            ohlcv = self.exchange.fetch_ohlcv(
                f'{symbol}/USD',
                '15m',  # 15-minute intervals
                limit=100  # Last 100 candles
            )
            
            # Convert to DataFrame
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # Calculate indicators
            # Trend Indicators
            macd = MACD(close=df['close'])
            df['macd'] = macd.macd()
            df['macd_signal'] = macd.macd_signal()
            
            sma_20 = SMAIndicator(close=df['close'], window=20)
            df['sma_20'] = sma_20.sma_indicator()
            
            ema_20 = EMAIndicator(close=df['close'], window=20)
            df['ema_20'] = ema_20.ema_indicator()
            
            # Momentum Indicators
            rsi = RSIIndicator(close=df['close'])
            df['rsi'] = rsi.rsi()
            
            stoch = StochasticOscillator(high=df['high'], low=df['low'], close=df['close'])
            df['stoch_k'] = stoch.stoch()
            df['stoch_d'] = stoch.stoch_signal()
            
            # Volatility Indicators
            bb = BollingerBands(close=df['close'])
            df['bb_high'] = bb.bollinger_hband()
            df['bb_mid'] = bb.bollinger_mavg()
            df['bb_low'] = bb.bollinger_lband()
            
            # Volume Indicators
            vwap = VolumeWeightedAveragePrice(
                high=df['high'],
                low=df['low'],
                close=df['close'],
                volume=df['volume']
            )
            df['vwap'] = vwap.volume_weighted_average_price()
            
            # Get the most recent values
            latest = df.iloc[-1]
            
            return {
                'trend': {
                    'macd': {
                        'value': latest['macd'],
                        'signal': latest['macd_signal'],
                        'histogram': latest['macd'] - latest['macd_signal']
                    },
                    'sma_20': latest['sma_20'],
                    'ema_20': latest['ema_20']
                },
                'momentum': {
                    'rsi': latest['rsi'],
                    'stochastic': {
                        'k': latest['stoch_k'],
                        'd': latest['stoch_d']
                    }
                },
                'volatility': {
                    'bollinger_bands': {
                        'high': latest['bb_high'],
                        'mid': latest['bb_mid'],
                        'low': latest['bb_low']
                    }
                },
                'volume': {
                    'vwap': latest['vwap']
                },
                'price': {
                    'current': latest['close'],
                    'open': latest['open'],
                    'high': latest['high'],
                    'low': latest['low']
                }
            }
        except Exception as e:
            print(f"Error calculating technical indicators for {symbol}: {e}")
            return None

    def get_all_indicators(self, symbols):
        """Calculate technical indicators for all symbols"""
        technical_analysis = {}
        for symbol in symbols:
            technical_analysis[symbol] = self.calculate_indicators(symbol)
        return technical_analysis
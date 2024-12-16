import os
import requests
import logging

class MarketData:
    def __init__(self, exchange):
        self.exchange = exchange

    def get_crypto_infos(self, symbols):
        infos = {}
        for symbol in symbols:
            try:
                ticker = self.exchange.fetch_ticker(f'{symbol}/USD')
                useful_info = {
                    'symbol': symbol,
                    'ask_price': ticker['ask'],
                    'bid_price': ticker['bid'],
                    'high_price': ticker['high'],
                    'low_price': ticker['low'],
                    'volume': ticker['baseVolume']
                }
                infos[symbol] = useful_info
            except Exception as e:
                logging.error(f"Error fetching info for {symbol}: {e}")
        return infos

    def get_historical_data(self, symbols):
        historicals = {}
        end_time = self.exchange.milliseconds()
        start_time = end_time - (7 * 24 * 60 * 60 * 1000)  # 7 days ago

        for symbol in symbols:
            try:
                ohlcv = self.exchange.fetch_ohlcv(
                    f'{symbol}/USD',
                    '10m',
                    since=start_time,
                    limit=1000
                )
                useful_data = []
                for candle in ohlcv:
                    useful_entry = {
                        'begins_at': self.exchange.iso8601(candle[0]),
                        'open_price': candle[1],
                        'high_price': candle[2],
                        'low_price': candle[3],
                        'close_price': candle[4],
                        'volume': candle[5],
                    }
                    useful_data.append(useful_entry)
                historicals[symbol] = useful_data
            except Exception as e:
                logging.error(f"Error fetching historical data for {symbol}: {e}")
        
        return historicals

    def get_all_crypto_news(self, symbols):
        API_KEY = os.getenv("NEWSAPI_KEY")
        all_news = {}

        for symbol in symbols:
            url = f'https://newsapi.org/v2/everything?q={symbol}&apiKey={API_KEY}'
            response = requests.get(url)
            data = response.json()
            
            news_data = []
            try:
                for article in data['articles'][:3]:  # Limit to top 3 articles
                    news_data.append({
                        'title': article['title'],
                        'source': article['source']['name'],
                    })
                all_news[symbol] = news_data
            except:
                logging.error(f"Error fetching news for {symbol}")
        return all_news
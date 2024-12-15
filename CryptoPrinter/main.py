import ccxt
import openai
import os
from datetime import datetime, timedelta
import time
import requests
import re

from mock_portfolio import MockPortfolio
from openai import OpenAI
from technical_analysis import TechnicalAnalysis

import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
        logging.StreamHandler()
    ]
)

# Initialize CCXT Kraken exchange
exchange = ccxt.kraken({
    'apiKey': os.getenv('KRAKEN_API_KEY'),
    'secret': os.getenv('KRAKEN_API_SECRET'),
})

# After initializing the exchange, create the technical analysis instance
technical_analyzer = TechnicalAnalysis(exchange)

# Create a global mock portfolio instance
mock_portfolio = MockPortfolio()

client = OpenAI()  # This will automatically use your OPENAI_API_KEY from environment variables

symbols = ["BTC", "ETH", "XRP", "SOL", "ADA", "AVAX", "LINK"]

PROMPT_FOR_AI = f"""
You are an advanced trading AI designed to maximize profits while minimizing risks in cryptocurrency trading. 

Your mission is to achieve the highest possible return over one month, trading the following cryptocurrencies: BTC, ETH, XRP, SOL, DOGE, ADA, AVAX, LINK, SHIB, XLM, and XTZ. 
You have access to real-time market data, technical indicators, and news.
For now, you will be using a mock portfolio that started with $10,000. In the future, you will be using a real portfolio.

Key Rules and Considerations

Risk Management:

Never risk more than 15% of the total account balance on any single trade.
Maintain a cash reserve of at least 20% of the total balance to capitalize on sudden opportunities.
Use stop-losses to limit losses on any trade to 3% of the total account balance.

Trading Strategies:

Use technical analysis (MACD, Bollinger Bands, Moving Averages, RSI, Stochastic Oscillators, Fibonacci Retracements) to identify trends and entry/exit points.
Incorporate news sentiment analysis to identify opportunities driven by breaking events or developments.
Trade only when there is a high-confidence setup based on a combination of technical and fundamental indicators.

Market Conditions:

Adapt strategies based on market trends (bullish, bearish, or sideways).

Decision Frequency:

Make decisions every 15 minutes based on updated data.
Avoid overtrading; do not execute more than 5 trades per hour unless there is an exceptionally strong rationale.

Execution Options:

buy_crypto_price(symbol, amount, summary): Buy cryptocurrency for a specified dollar amount.
buy_crypto_limit(symbol, amount, summary, limit): Set a limit order to buy at a specific price.
sell_crypto_price(symbol, amount, summary): Sell cryptocurrency for a specified dollar amount.
sell_crypto_limit(symbol, amount, summary, limit): Set a limit order to sell at a specific price.
cancel_order(orderId): Cancel an open order.
do_nothing(): Use when there are no clear opportunities.

Critical:

Base every decision on data provided (crypto info, balance, positions, historical data, news, open orders).
Provide only one command per response in the exact format: command("symbol", amount, summary, [optional limit]). The summary parameter is a 2-4 sentence explanation of the logic you're using on why you are making the trade.

Provided Data:

Crypto Info (symbol, ask_price, bid_price, high_price, low_price, volume)
Balance
Open Orders (id, type, side, quantity, price)
Positions (symbol, quantity, average_buy_price, cost_basis, portfolio_percentage)
Historical Data (10-minute interval for the past week: open, close, high, low, volume)
News Headlines (top 3 for each cryptocurrency, include sentiment analysis if possible)

The current date and time is {datetime.now().isoformat()}.

Your Objective: Make intelligent, data-driven decisions to maximize returns while protecting the account from excessive risk. Always prioritize profits and avoid overtrading.
"""

past_trades = []

def record_trade(action, symbol, amount, summary, limit=None):
    trade_info = {
        "action": action,
        "symbol": symbol,
        "amount": amount,
        "descriptionOfWhyTradeMade": summary,
        "time": datetime.now().isoformat(),
    }
    if limit is not None:
        trade_info["limit"] = limit
    past_trades.append(trade_info)
    if len(past_trades) > 10:  # keep only the last 10 trades
        past_trades.pop(0)

def get_crypto_infos():
    infos = {}
    for symbol in symbols:
        try:
            ticker = exchange.fetch_ticker(f'{symbol}/USD')
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
            print(f"Error fetching info for {symbol}: {e}")
    return infos

def get_balance():
    return mock_portfolio.get_balance()

def buy_crypto_price(symbol, amount, summary):
    amount = float(amount)
    try:
        ticker = exchange.fetch_ticker(f'{symbol}/USD')  # Still get real price data
        order = mock_portfolio.create_market_buy_order(symbol, amount, ticker['ask'])
        record_trade("buy_crypto_price", symbol, amount, summary)
        print(order)
    except Exception as e:
        print(f"Error buying {symbol}: {e}")

def sell_crypto_price(symbol, amount, summary):
    amount = float(amount)
    try:
        ticker = exchange.fetch_ticker(f'{symbol}/USD')  # Still get real price data
        order = mock_portfolio.create_market_sell_order(symbol, amount, ticker['bid'])
        record_trade("sell_crypto_price", symbol, amount, summary)
        print(order)
    except Exception as e:
        print(f"Error selling {symbol}: {e}")

def buy_crypto_limit(symbol, amount, summary, limit):
    amount = float(amount)
    limit = float(limit)
    try:
        order = mock_portfolio.create_limit_buy_order(symbol, amount, limit)
        record_trade("buy_crypto_limit", symbol, amount, summary, limit)
        print(order)
    except Exception as e:
        print(f"Error placing limit buy for {symbol}: {e}")

def sell_crypto_limit(symbol, amount, summary, limit):
    amount = float(amount)
    limit = float(limit)
    try:
        order = mock_portfolio.create_limit_sell_order(symbol, amount, limit)
        record_trade("sell_crypto_limit", symbol, amount, summary, limit)
        print(order)
    except Exception as e:
        print(f"Error placing limit sell for {symbol}: {e}")

def get_positions():
    return mock_portfolio.get_positions()

def get_open_orders():
    return mock_portfolio.get_open_orders()

def cancel_order(orderId):
    try:
        mock_portfolio.cancel_order(orderId)
    except Exception as e:
        print(f"Error canceling order {orderId}: {e}")

def get_historical_data():
    historicals = {}
    end_time = exchange.milliseconds()
    start_time = end_time - (7 * 24 * 60 * 60 * 1000)  # 7 days ago

    for symbol in symbols:
        try:
            ohlcv = exchange.fetch_ohlcv(
                f'{symbol}/USD',
                '10m',
                since=start_time,
                limit=1000
            )
            useful_data = []
            for candle in ohlcv:
                useful_entry = {
                    'begins_at': exchange.iso8601(candle[0]),
                    'open_price': candle[1],
                    'high_price': candle[2],
                    'low_price': candle[3],
                    'close_price': candle[4],
                    'volume': candle[5],
                }
                useful_data.append(useful_entry)
            historicals[symbol] = useful_data
        except Exception as e:
            print(f"Error fetching historical data for {symbol}: {e}")
    
    return historicals

def get_all_crypto_news():
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
            return all_news

    return all_news

def get_trade_advice():
    # Get all the necessary information
    crypto_info = get_crypto_infos()
    balance = get_balance()
    positions = get_positions()
    news = get_all_crypto_news()
    open_orders = get_open_orders()
    past_trade_info = '\n'.join([str(trade) for trade in past_trades])
    
    # Get technical indicators for each symbol
    technical_analysis = technical_analyzer.get_all_indicators(symbols)

    # Convert the info into a format suitable for the AI prompt
    info_str = (
        f"Crypto Info: {crypto_info}\n"
        f"Technical Analysis: {technical_analysis}\n"
        f"Balance: {balance}\n"
        f"Positions: {positions}\n"
        f"News: {news}\n"
        f"Open Orders: {open_orders}\n"
        f"Past Trades: {past_trade_info}"
    )
    
    prompt = PROMPT_FOR_AI + "\n\n" + info_str
    user_prompt = """
What should we do to make the most amount of profit based on the info provided?

buy_crypto_price(symbol, amount) This will buy the specified dollars of the specified cryptocurrency.
buy_crypto_limit(symbol, amount, limit) This will set a limit order to buy the specified dollars of the specified cryptocurrency if it reaches the specified limit.
sell_crypto_price(symbol, amount) This will sell the specified dollars of the specified cryptocurrency.
sell_crypto_limit(symbol, amount, limit) This will set a limit order to sell the specified dollars of the specified cryptocurrency if it reaches the specified limit.
cancel_order(orderId) This will cancel the specified order.
do_nothing() Use this when you don't see any necessary changes.

CRITICAL: RESPOND IN ONLY THE ABOVE FORMAT. EXAMPLE: buy_crypto_price("BTC", 30). ONLY RESPOND WITH ONE COMMAND.
    """

    # Feed the prompt to the AI
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature = 0.2,
    )
    res = response.choices[0].message["content"]
    res = res.replace("\\", "")
    return res

def execute_response(response):
    match = re.match(r'(\w+)\((.*?)\)', response)
    if match:
        command = match.group(1)
        args = [arg.strip().strip('\"') for arg in match.group(2).split(',')]  # remove surrounding quotation marks
        if len(args) == 1:
            print("Doing nothing...")
            return
        command_map = {
            "buy_crypto_price": buy_crypto_price,
            "buy_crypto_limit": buy_crypto_limit,
            "sell_crypto_price": sell_crypto_price,
            "sell_crypto_limit": sell_crypto_limit,
            "cancel_order": cancel_order,
            "do_nothing": lambda: None  # no action needed
        }
        function_to_execute = command_map.get(command)  # retrieves the function from command_map dictionary
        if function_to_execute:
            print(f"Executing command {function_to_execute} with args {args} in 5 seconds.")
            time.sleep(5)
            function_to_execute(*args)  # executes the function with its arguments
        else:
            print("Invalid command:", command)
    else:
        print("Invalid response, retrying:", response)
        time.sleep(10)
        execute_response(get_trade_advice())

while True:
    execute_response(get_trade_advice())
    time.sleep(900)

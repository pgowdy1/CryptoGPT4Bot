import logging
import time

class TradeExecutor:
    def __init__(self, portfolio, exchange):
        self.portfolio = portfolio
        self.exchange = exchange

    def execute_buy_market(self, symbol, amount, summary):
        amount = float(amount)
        try:
            ticker = self.exchange.fetch_ticker(f'{symbol}/USD')
            order = self.portfolio.create_market_buy_order(symbol, amount, ticker['ask'])
            if order:
                self.portfolio.record_trade("buy_market", symbol, amount, order['quantity'], ticker['ask'], summary)
            logging.info(f"Executed market buy: {order}")
            return order
        except Exception as e:
            logging.error(f"Error buying {symbol}: {e}")
            return None

    def execute_sell_market(self, symbol, amount, summary):
        amount = float(amount)
        try:
            ticker = self.exchange.fetch_ticker(f'{symbol}/USD')
            order = self.portfolio.create_market_sell_order(symbol, amount, ticker['bid'])
            if order:
                self.portfolio.record_trade("sell_market", symbol, amount, order['quantity'], ticker['bid'], summary)
            logging.info(f"Executed market sell: {order}")
            return order
        except Exception as e:
            logging.error(f"Error selling {symbol}: {e}")
            return None

    def execute_buy_limit(self, symbol, amount, summary, limit):
        amount = float(amount)
        limit = float(limit)
        try:
            order = self.portfolio.create_limit_buy_order(symbol, amount, limit)
            logging.info(f"Created limit buy order: {order}")
            return order
        except Exception as e:
            logging.error(f"Error placing limit buy for {symbol}: {e}")
            return None

    def execute_sell_limit(self, symbol, amount, summary, limit):
        amount = float(amount)
        limit = float(limit)
        try:
            order = self.portfolio.create_limit_sell_order(symbol, amount, limit)
            logging.info(f"Created limit sell order: {order}")
            return order
        except Exception as e:
            logging.error(f"Error placing limit sell for {symbol}: {e}")
            return None

    def cancel_order(self, order_id):
        try:
            return self.portfolio.cancel_order(order_id)
        except Exception as e:
            logging.error(f"Error canceling order {order_id}: {e}")
            return False
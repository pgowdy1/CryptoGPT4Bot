from datetime import datetime
import logging

class LivePortfolio:
    def __init__(self, exchange):
        self.exchange = exchange
        self.trade_history = []

    def get_balance(self):
        try:
            balance = self.exchange.fetch_balance()
            return float(balance['USD']['free'])
        except Exception as e:
            logging.error(f"Error fetching balance: {e}")
            return 0.0

    def get_positions(self):
        try:
            balance = self.exchange.fetch_balance()
            positions = []
            for symbol in balance:
                if symbol != 'USD' and balance[symbol]['free'] > 0:
                    ticker = self.exchange.fetch_ticker(f'{symbol}/USD')
                    positions.append({
                        'symbol': symbol,
                        'quantity': float(balance[symbol]['free']),
                        'dollar_amount': float(balance[symbol]['free']) * ticker['last']
                    })
            return positions
        except Exception as e:
            logging.error(f"Error fetching positions: {e}")
            return []

    def create_market_buy_order(self, symbol, amount, price):
        try:
            order = self.exchange.create_market_buy_order(f'{symbol}/USD', amount, {'trading_agreement': 'agree'})
            return {
                'symbol': symbol,
                'amount': float(order['cost']),
                'quantity': float(order['filled']),
                'price': float(order['average'])
            }
        except Exception as e:
            logging.error(f"Error creating market buy order: {e}")
            return None

    def create_market_sell_order(self, symbol, amount, price):
        try:
            order = self.exchange.create_market_sell_order(f'{symbol}/USD', amount, {'trading_agreement': 'agree'})
            return {
                'symbol': symbol,
                'amount': float(order['cost']),
                'quantity': float(order['filled']),
                'price': float(order['average'])
            }
        except Exception as e:
            logging.error(f"Error creating market sell order: {e}")
            return None

    def create_limit_buy_order(self, symbol, amount, limit_price):
        try:
            order = self.exchange.create_limit_buy_order(f'{symbol}/USD', amount, limit_price, {'trading_agreement': 'agree'})
            return order
        except Exception as e:
            logging.error(f"Error creating limit buy order: {e}")
            return None

    def create_limit_sell_order(self, symbol, amount, limit_price):
        try:
            order = self.exchange.create_limit_sell_order(f'{symbol}/USD', amount, limit_price, {'trading_agreement': 'agree'})
            return order
        except Exception as e:
            logging.error(f"Error creating limit sell order: {e}")
            return None

    def get_open_orders(self):
        try:
            orders = self.exchange.fetch_open_orders()
            return [{
                'id': order['id'],
                'symbol': order['symbol'].split('/')[0],
                'type': order['type'],
                'side': order['side'],
                'amount': float(order['amount']),
                'price': float(order['price'])
            } for order in orders]
        except Exception as e:
            logging.error(f"Error fetching open orders: {e}")
            return []

    def cancel_order(self, order_id):
        try:
            return self.exchange.cancel_order(order_id)
        except Exception as e:
            logging.error(f"Error canceling order: {e}")
            return False

    def record_trade(self, command, symbol, amount, quantity, price, summary):
        trade_record = {
            'timestamp': datetime.now().isoformat(),
            'command': command,
            'success': True,
            'type': 'market' if 'market' in command else 'limit',
            'symbol': symbol,
            'amount': amount,
            'quantity': quantity,
            'price': price,
            'ai_reasoning': summary
        }
        self.trade_history.append(trade_record)

    def get_trade_history(self):
        """Get recent trade history"""
        try:
            formatted_trades = []
            # Get trades for each symbol
            for symbol in ['BTC/USD', 'ETH/USD', 'XRP/USD', 'SOL/USD', 'DOGE/USD', 
                          'ADA/USD', 'AVAX/USD', 'LINK/USD', 'SHIB/USD', 'XLM/USD', 'XTZ/USD']:
                trades = self.exchange.fetch_my_trades(symbol, limit=20)
                for trade in trades:
                    formatted_trades.append({
                        'timestamp': trade['datetime'],
                        'command': 'market_buy' if trade['side'] == 'buy' else 'market_sell',
                        'symbol': trade['symbol'].split('/')[0],
                        'amount': float(trade['cost']),  # USD amount
                        'quantity': float(trade['amount']),  # Crypto amount
                        'price': float(trade['price']),
                        'success': True
                    })
            
            # Sort by timestamp and return most recent 20
            formatted_trades.sort(key=lambda x: x['timestamp'], reverse=True)
            return formatted_trades[:20]
        except Exception as e:
            logging.error(f"Error fetching trade history: {e}")
            return []
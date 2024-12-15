from datetime import datetime
import robin_stocks.robinhood as rh

class MockPortfolio:
    def __init__(self, initial_balance=10000):
        self.balance = initial_balance
        self.positions = {}  # {symbol: {'quantity': float, 'average_price': float}}
        self.trade_history = []
        self.open_orders = []

    def record_trade(self, trade_type, symbol, amount, price, summary):
        self.trade_history.append({
            'time': datetime.now().isoformat(),
            'type': trade_type,
            'symbol': symbol,
            'amount': amount,
            'price': price,
            'summary': summary
        })

    def get_portfolio_value(self):
        total_value = self.balance
        for symbol, position in self.positions.items():
            current_price = float(rh.get_crypto_quote(symbol)['mark_price'])
            total_value += position['quantity'] * current_price
        return total_value

    def print_portfolio_status(self):
        print("\n=== Portfolio Status ===")
        print(f"Cash Balance: ${self.balance:.2f}")
        total_value = self.balance
        
        for symbol, position in self.positions.items():
            current_price = float(rh.get_crypto_quote(symbol)['mark_price'])
            position_value = position['quantity'] * current_price
            total_value += position_value
            profit_loss = position_value - (position['quantity'] * position['average_price'])
            print(f"{symbol}: {position['quantity']:.8f} units @ ${position['average_price']:.2f} avg price")
            print(f"Current Value: ${position_value:.2f} (P/L: ${profit_loss:.2f})")
        
        print(f"\nTotal Portfolio Value: ${total_value:.2f}")
        print("=====================\n")
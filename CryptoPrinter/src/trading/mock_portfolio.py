import json
import logging
import os
from datetime import datetime

class MockPortfolio:
    def __init__(self, initial_balance=10000, data_file='mock_portfolio_data.json'):
        self.data_file = data_file
        
        # Load existing data or create new portfolio
        if os.path.exists(data_file):
            self.load_portfolio()
        else:
            self.balance = initial_balance
            self.positions = {}  # {symbol: {'quantity': float, 'average_price': float}}
            self.open_orders = []  # List of open limit orders
            self.trade_history = []  # List of executed trades
            self.save_portfolio()
            
    def load_portfolio(self):
        with open(self.data_file, 'r') as f:
            data = json.load(f)
            self.balance = data['balance']
            self.positions = data['positions']
            self.open_orders = data['open_orders']
            self.trade_history = data.get('trade_history', [])  # backwards compatibility
            
    def save_portfolio(self):
        try:
            with open(self.data_file, 'w') as f:
                json.dump({
                    'balance': self.balance,
                    'positions': self.positions,
                    'open_orders': self.open_orders,
                    'trade_history': self.trade_history,
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            print(f"Error saving portfolio data: {e}")
            
    def record_trade(self, command, symbol, amount, quantity, price, summary):
        """Record a single trade with its result"""
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
        self.save_portfolio()
        
    def get_balance(self):
        return float(self.balance)
        
    def get_positions(self):
        return [
            {
                'symbol': symbol,
                'quantity': details['quantity'],
                'dollar_amount': details['quantity'] * details['average_price']
            }
            for symbol, details in self.positions.items()
            if details['quantity'] > 0
        ]

    def create_market_buy_order(self, symbol, amount, price):
        try:
            # Convert amount to float
            amount = float(amount)
            price = float(price)
            
            if amount > self.balance:
                raise Exception(f"Insufficient funds: have ${self.balance}, need ${amount}")
                
            quantity = amount / price
            if symbol not in self.positions:
                self.positions[symbol] = {'quantity': 0, 'average_price': 0}
                
            # Update position with new purchase
            current_value = self.positions[symbol]['quantity'] * self.positions[symbol]['average_price']
            new_value = amount
            total_quantity = self.positions[symbol]['quantity'] + quantity
            
            self.positions[symbol]['average_price'] = (current_value + new_value) / total_quantity
            self.positions[symbol]['quantity'] = total_quantity
            
            self.balance -= amount
            
            # Save after updating
            self.save_portfolio()
            
            return {
                'symbol': symbol,
                'amount': amount,
                'quantity': quantity,
                'price': price
            }
        except Exception as e:
            print(f"Error executing market buy order: {e}")
            return None
        
    def create_market_sell_order(self, symbol, amount, price):
        try:
            # Convert amount to float
            amount = float(amount)
            price = float(price)
            
            if symbol not in self.positions or self.positions[symbol]['quantity'] <= 0:
                raise Exception("No position to sell")
                
            quantity = amount / price
            if quantity > self.positions[symbol]['quantity']:
                raise Exception(f"Insufficient crypto quantity: have {self.positions[symbol]['quantity']}, need {quantity}")
                
            self.positions[symbol]['quantity'] -= quantity
            self.balance += amount
            
            # Save after updating
            self.save_portfolio()
            
            return {
                'symbol': symbol,
                'amount': amount,
                'quantity': quantity,
                'price': price
            }
        except Exception as e:
            logging.error(f"Error executing market sell order: {e}")
            return None
        
    def create_limit_buy_order(self, symbol, amount, limit_price):
        if amount > self.balance:
            raise Exception("Insufficient funds")
            
        order = {
            'id': len(self.open_orders),
            'symbol': symbol,
            'type': 'limit',
            'side': 'buy',
            'amount': amount,
            'price': limit_price,
            'status': 'open',
            'created_at': datetime.now().isoformat()
        }
        self.open_orders.append(order)
        self.save_portfolio()
        return order
        
    def create_limit_sell_order(self, symbol, amount, limit_price):
        if symbol not in self.positions or self.positions[symbol]['quantity'] <= 0:
            raise Exception("No position to sell")
            
        order = {
            'id': len(self.open_orders),
            'symbol': symbol,
            'type': 'limit',
            'side': 'sell',
            'amount': amount,
            'price': limit_price,
            'status': 'open',
            'created_at': datetime.now().isoformat()
        }
        self.open_orders.append(order)
        self.save_portfolio()
        return order
        
    def get_open_orders(self):
        return [
            {
                'id': order['id'],
                'type': order['type'],
                'side': order['side'],
                'quantity': order['amount'],
                'price': order['price']
            }
            for order in self.open_orders
            if order['status'] == 'open'
        ]
        
    def cancel_order(self, order_id):
        for order in self.open_orders:
            if order['id'] == order_id:
                order['status'] = 'cancelled'
                self.save_portfolio()
                return True
        return False
        
    def get_trade_history(self):
        return self.trade_history
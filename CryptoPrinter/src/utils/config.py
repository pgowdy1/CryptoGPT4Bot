import os
from dotenv import load_dotenv

class Config:
    def __init__(self):
        load_dotenv()
        
        # API Keys
        self.OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
        self.KRAKEN_API_KEY = os.getenv('KRAKEN_API_KEY')
        self.KRAKEN_API_SECRET = os.getenv('KRAKEN_API_SECRET')
        self.NEWSAPI_KEY = os.getenv('NEWSAPI_KEY')
        
        # Trading Parameters
        self.TRADE_INTERVAL = int(os.getenv('TRADE_INTERVAL', 900))
        
        # Trading Symbols
        self.SYMBOLS = ["BTC", "ETH", "XRP", "SOL", "DOGE", "ADA", "AVAX", "LINK", "SHIB", "XLM", "XTZ"]
        
        # File Paths
         # File Paths
        self.BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.MOCK_PORTFOLIO_FILE = os.path.join(self.BASE_DIR, 'data', 'mock_portfolio_data.json')
        self.LOG_FILE = os.path.join(self.BASE_DIR, 'logs', 'trading_bot.log')
        
        # Trading Mode
        self.TRADING_MODE = os.getenv('TRADING_MODE', 'mock')  # 'mock' or 'live'
        self.INITIAL_MOCK_BALANCE = float(os.getenv('INITIAL_MOCK_BALANCE', '10000'))
        
        # Validate configuration
        if self.TRADING_MODE == 'live':
            assert self.KRAKEN_API_KEY, "Kraken API key required for live trading"
            assert self.KRAKEN_API_SECRET, "Kraken API secret required for live trading"
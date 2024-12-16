import logging
import ccxt
import time
from openai import OpenAI
import re

from src.utils.config import Config
from src.utils.logger import setup_logger
from src.trading.mock_portfolio import MockPortfolio
from src.trading.technical_analysis import TechnicalAnalysis
from src.trading.trade_executor import TradeExecutor
from src.data.market_data import MarketData
from src.ai.advisor import TradingAdvisor

def main():
    # Initialize configuration and logging
    config = Config()
    logger = setup_logger()
    
    # Initialize exchange
    exchange = ccxt.kraken({
        'apiKey': config.KRAKEN_API_KEY,
        'secret': config.KRAKEN_API_SECRET,
    })
    
    # Initialize components
    portfolio = MockPortfolio(config.MOCK_PORTFOLIO_FILE)
    technical_analyzer = TechnicalAnalysis(exchange)
    market_data = MarketData(exchange)
    trade_executor = TradeExecutor(portfolio, exchange)
    advisor = TradingAdvisor(OpenAI())
    
    logger.info("Trading bot initialized successfully.")

    while True:
        try:
            start_time = time.time()
            
            # Gather all necessary data
            crypto_infos = market_data.get_crypto_infos(config.SYMBOLS)
            technical_analysis = technical_analyzer.get_all_indicators(config.SYMBOLS)
            news = market_data.get_all_crypto_news(config.SYMBOLS)
            
            # Get portfolio status
            portfolio_data = {
                'balance': portfolio.get_balance(),
                'positions': portfolio.get_positions(),
                'open_orders': portfolio.get_open_orders()
            }
            
            # Get AI advice
            advice = advisor.get_advice(crypto_infos, portfolio_data, technical_analysis, news)
            
            if advice:
                parse_and_execute_response(advice, trade_executor)
            
            # Calculate wait time
            elapsed_time = time.time() - start_time
            wait_time = max(0, config.TRADE_INTERVAL - elapsed_time)
            logger.info(f"Waiting {wait_time:.2f} seconds until next trade check")
            time.sleep(wait_time)
            
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            time.sleep(60)  # Wait a minute before retrying on error

if __name__ == "__main__":
    main()

def parse_and_execute_response(response, trade_executor):
    lines = response.split('\n')
    command_line = None
    for line in reversed(lines):
        if any(cmd in line.lower() for cmd in ["buy_crypto_price", "sell_crypto_price", "buy_crypto_limit", "sell_crypto_limit", "cancel_order", "do_nothing"]):
            command_line = line
            break
    
    if not command_line:
        logging.error(f"No valid command found in response: {response}")
        return False

    match = re.match(r'.*?(buy_crypto_price|sell_crypto_price|buy_crypto_limit|sell_crypto_limit|cancel_order|do_nothing)\((.*)\)', command_line)
    
    if not match:
        logging.error(f"Invalid response format: {command_line}")
        return False

    command = match.group(1)
    args_str = match.group(2)
    args = []
    current_arg = ''
    in_quotes = False
    quote_char = None
    
    for char in args_str:
        if char in ['"', "'"]:
            if not in_quotes:
                in_quotes = True
                quote_char = char
            elif char == quote_char:
                in_quotes = False
            current_arg += char
        elif char == ',' and not in_quotes:
            args.append(current_arg.strip().strip('"\''))
            current_arg = ''
        else:
            current_arg += char
    
    if current_arg:
        args.append(current_arg.strip().strip('"\''))

    command_map = {
        "buy_crypto_price": trade_executor.execute_buy_market,
        "buy_crypto_limit": trade_executor.execute_buy_limit,
        "sell_crypto_price": trade_executor.execute_sell_market,
        "sell_crypto_limit": trade_executor.execute_sell_limit,
        "cancel_order": trade_executor.cancel_order,
        "do_nothing": lambda: None
    }

    function_to_execute = command_map.get(command)
    if function_to_execute:
        logging.info(f"Executing command {command} with args {args}")
        function_to_execute(*args)
        return True
    else:
        logging.error(f"Invalid command: {command}")
        return False


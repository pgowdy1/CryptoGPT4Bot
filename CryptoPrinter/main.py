import logging
import ccxt
import time
from openai import OpenAI
import re
from datetime import datetime

from src.utils.config import Config
from src.utils.logger import setup_logger
from src.trading.mock_portfolio import MockPortfolio
from src.trading.technical_analysis import TechnicalAnalysis
from src.trading.trade_executor import TradeExecutor
from src.data.market_data import MarketData
from src.ai.advisor import TradingAdvisor
from src.trading.live_portfolio import LivePortfolio

def parse_and_execute_response(response, trade_executor):
    lines = response.split('\n')
    commands_executed = 0
    success = False

    for line in lines:
        # Skip empty lines and lines that don't contain commands
        if not line.strip() or not any(cmd in line.lower() for cmd in ["buy_crypto_price", "sell_crypto_price", "buy_crypto_limit", "sell_crypto_limit", "cancel_order", "do_nothing"]):
            continue

        match = re.match(r'.*?(buy_crypto_price|sell_crypto_price|buy_crypto_limit|sell_crypto_limit|cancel_order|do_nothing)\((.*)\)', line)
        
        if not match:
            logging.error(f"Invalid response format in line: {line}")
            continue

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
            try:
                if function_to_execute(*args):
                    commands_executed += 1
                    success = True
            except Exception as e:
                logging.error(f"Error executing command {command}: {e}")

    logging.info(f"Executed {commands_executed} commands successfully")
    return success

def main():
    # Initialize configuration and logging
    config = Config()
    logger = setup_logger()
    
    # Add a separate logger for AI interactions
    ai_logger = logging.getLogger('ai_interactions')
    ai_handler = logging.FileHandler('logs/ai_interactions.log')
    ai_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    ai_logger.addHandler(ai_handler)
    ai_logger.setLevel(logging.DEBUG)
    
    # Initialize exchange
    exchange = ccxt.kraken({
        'apiKey': config.KRAKEN_API_KEY,
        'secret': config.KRAKEN_API_SECRET,
    })
    
    # Initialize portfolio based on trading mode
    if config.TRADING_MODE == 'live':
        logger.info("Initializing LIVE trading mode")
        portfolio = LivePortfolio(exchange)
    else:
        logger.info("Initializing MOCK trading mode")
        portfolio = MockPortfolio(
            initial_balance=config.INITIAL_MOCK_BALANCE,
            data_file='data/mock_portfolio_data.json'
        )
    technical_analyzer = TechnicalAnalysis(exchange)
    market_data = MarketData(exchange)
    trade_executor = TradeExecutor(portfolio, exchange)
    advisor = TradingAdvisor(OpenAI())
    
    logger.info("Trading bot initialized successfully.")

    while True:
        try:
            start_time = time.time()
            
            # Log the start of a new trading cycle
            logger.info("Starting new trading cycle")
            
            # Gather all necessary data
            crypto_infos = market_data.get_crypto_infos(config.SYMBOLS)
            logger.debug(f"Gathered crypto info: {crypto_infos}")
            
            technical_analysis = technical_analyzer.get_all_indicators(config.SYMBOLS)
            logger.debug(f"Technical analysis results: {technical_analysis}")
            
            # Get portfolio status
            portfolio_data = {
                'balance': float(portfolio.get_balance()),
                'positions': portfolio.get_positions(),
                'open_orders': portfolio.get_open_orders(),
                'trade_history': portfolio.get_trade_history()
            }
            logger.debug(f"Current portfolio status: {portfolio_data}")
            
            # Log AI input data
            ai_logger.info("=== New AI Consultation ===")
            ai_logger.info(f"Input - Crypto Info: {crypto_infos}")
            ai_logger.info("=== Portfolio Status ===")
            ai_logger.info(f"Balance: ${portfolio_data['balance']:.2f}")
            ai_logger.info("Positions:")
            for position in portfolio_data['positions']:
                ai_logger.info(f"  {position['symbol']}: {position['quantity']:.8f} (${float(position['dollar_amount']):.2f})")
            ai_logger.info("Open Orders:")
            for order in portfolio_data['open_orders']:
                ai_logger.info(f"  {order['side'].upper()} {order['type']} - {order['quantity']} {order['id']} @ ${float(order['price']):.2f}")
            ai_logger.info(f"Input - Technical Analysis: {technical_analysis}")
            
            # Get AI advice
            advice = advisor.get_advice(crypto_infos, portfolio_data, technical_analysis)
            
            # Log AI response and execution
            ai_logger.info(f"=== AI Response ===")
            ai_logger.info(f"Full Response:\n{advice}")
            
            if advice:
                # Split advice into individual commands
                commands = [line.strip() for line in advice.split('\n') if line.strip()]
                ai_logger.info(f"Number of commands detected: {len(commands)}")
                
                for i, command in enumerate(commands, 1):
                    ai_logger.info(f"Processing command {i}/{len(commands)}: {command}")
                    try:
                        execution_result = parse_and_execute_response(command, trade_executor)
                        ai_logger.info(f"Command {i} execution result: {'Success' if execution_result else 'Failed'}")
                    except Exception as e:
                        ai_logger.error(f"Error executing command {i}: {e}")
                
                # Log updated portfolio status after all commands
                updated_portfolio = {
                    'balance': float(portfolio.get_balance()),
                    'positions': portfolio.get_positions(),
                    'open_orders': portfolio.get_open_orders()
                }
                ai_logger.info("=== Portfolio After Execution ===")
                ai_logger.info(f"Balance: ${updated_portfolio['balance']:.2f}")
                ai_logger.info("Positions:")
                for position in updated_portfolio['positions']:
                    ai_logger.info(f"  {position['symbol']}: {position['quantity']:.8f} (${float(position['dollar_amount']):.2f})")
                ai_logger.info("Open Orders:")
                for order in updated_portfolio['open_orders']:
                    ai_logger.info(f"  {order['side'].upper()} {order['type']} - {order['quantity']} {order['id']} @ ${float(order['price']):.2f}")
            
            # Calculate and log wait time
            elapsed_time = time.time() - start_time
            wait_time = max(0, config.TRADE_INTERVAL - elapsed_time)
            logger.info(f"Cycle completed in {elapsed_time:.2f}s. Waiting {wait_time:.2f}s until next cycle")
            
            # Log cycle summary
            ai_logger.info(f"=== Cycle Summary ===")
            ai_logger.info(f"Cycle duration: {elapsed_time:.2f}s")
            ai_logger.info(f"Portfolio after cycle: {portfolio.get_balance()}")
            ai_logger.info("=" * 50 + "\n")
            
            time.sleep(wait_time)
            
        except Exception as e:
            error_msg = f"Error in main loop: {str(e)}"
            logger.error(error_msg)
            ai_logger.error(error_msg)
            time.sleep(60)

if __name__ == "__main__":
    main()

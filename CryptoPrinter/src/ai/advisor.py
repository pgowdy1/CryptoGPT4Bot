from datetime import datetime
import logging

class TradingAdvisor:
    def __init__(self, client):
        self.client = client
        self.setup_prompt()

    def setup_prompt(self):
        self.base_prompt = """
You are an advanced trading AI designed to maximize profits while minimizing risks in cryptocurrency trading. 

Your mission is to achieve the highest possible return over one week, trading the following cryptocurrencies: BTC, ETH, XRP, SOL, DOGE, ADA, AVAX, LINK, SHIB, XLM, and XTZ. 
You have access to real-time market data and technical indicators.

CURRENT PORTFOLIO LIMITS:
Cash Available: ${balance:.2f}
Current Holdings:
{holdings}

Key Rules and Considerations:
1. You can only sell up to the amount you hold for each crypto.
2. You can only buy up to what your cash balance allows.
3. Use technical analysis to identify high-confidence setups.
4. Adapt to market conditions (bullish, bearish, sideways).
5. Make decisions every 30 minutes based on updated data.
6. Avoid overtrading (max 10 trades per hour).
7. We have a small portfolio, but we still need to make money. 

The current date and time is {current_time}.

EXAMPLES:
- If you hold 40 XTZ, you cannot sell 50 XTZ.
- If you have $100 cash, you cannot buy $150 worth of BTC.
"""

        self.user_prompt = """
What actions should we take to maximize profit over the next month based on the provided information?

You can respond with MULTIPLE COMMANDS, one per line. Valid commands are:
buy_crypto_price("symbol", units, "single summary string")
buy_crypto_limit("symbol", units, "single summary string", limit)
sell_crypto_price("symbol", units, "single summary string")
sell_crypto_limit("symbol", units, "single summary string", limit)
cancel_order(orderId)
do_nothing()

Example of multiple commands:
buy_crypto_price("BTC", 0.0003, "Strong bullish momentum")
sell_crypto_limit("ETH", 1.2, "Taking profits at resistance", 2250)
cancel_order(123)

So in this case, we're buying 0.0003 BTC at the current price, and selling 1.2 ETH at 2250.

IMPORTANT: Each command must be on a new line and include a summary string in quotes for trades.

Finally, on the last line, respond with a five sentence summary of the actions you're taking and the reasoning behind them.
"""

    def get_advice(self, market_data, portfolio_data, technical_analysis):
        current_time = datetime.now().isoformat()
        
        # Initialize holdings_str before using it
        holdings_str = ""
        
        # Log the input data
        logging.info("=== AI Trading Analysis Start ===")
        logging.info(f"Time: {current_time}")
        logging.info(f"Portfolio Balance: ${portfolio_data['balance']:.2f}")
        logging.info("Current Positions:")
        
        # Build the holdings string
        for position in portfolio_data['positions']:
            holdings_str += f"- {position['symbol']}: {position['quantity']:.8f} (${float(position['dollar_amount']):.2f})\n"
            logging.info(f"  {position['symbol']}: {position['quantity']:.8f} units")
        
        # Construct the full prompt with current data
        full_prompt = self.base_prompt.format(
            current_time=current_time,
            balance=portfolio_data['balance'],
            holdings=holdings_str
        )
        data_prompt = f"""
Current Market Data: {market_data}
Technical Analysis: {technical_analysis}
Portfolio Status: {portfolio_data}
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": full_prompt + data_prompt},
                    {"role": "user", "content": self.user_prompt}
                ],
                temperature=0.2,
            )
            
            ai_response = response.choices[0].message.content
            
            # Log the AI's response
            logging.info("=== AI Decision ===")
            logging.info(f"Full Response:\n{ai_response}")
            logging.info("==================\n")
            
            return ai_response
        except Exception as e:
            logging.error(f"Error getting AI advice: {e}")
            return None
from datetime import datetime
import logging

class TradingAdvisor:
    def __init__(self, client):
        self.client = client
        self.setup_prompt()

    def setup_prompt(self):
        self.base_prompt = """
You are an advanced trading AI designed to maximize profits while minimizing risks in cryptocurrency trading. 

Your mission is to achieve the highest possible return over one month, trading the following cryptocurrencies: BTC, ETH, XRP, SOL, DOGE, ADA, AVAX, LINK, SHIB, XLM, and XTZ. 
You have access to real-time market data and technical indicators.
You will be using a mock portfolio that starts with $10,000.

Key Rules and Considerations:
1. Never risk more than 15% of the total account balance on any single trade
2. Maintain a cash reserve of at least 20% to capitalize on opportunities
3. Use stop-losses to limit losses to 3% of total account balance
4. Use technical analysis
5. Use high-confidence setups
6. Adapt to market conditions (bullish, bearish, sideways)
7. Make decisions every 15 minutes based on updated data
8. Only sell crypto that you have in your portfolio -- in the past you've tried to sell crypto that you didn't have in your portfolio and it's led to losses
9. Avoid overtrading (max 10 trades per hour)

The current date and time is {current_time}.
"""

        self.user_prompt = """
What actions should we take to maximize profit based on the provided information?

You can respond with MULTIPLE COMMANDS, one per line. Valid commands are:
buy_crypto_price("symbol", amount, "single summary string")
buy_crypto_limit("symbol", amount, "single summary string", limit)
sell_crypto_price("symbol", amount, "single summary string")
sell_crypto_limit("symbol", amount, "single summary string", limit)
cancel_order(orderId)
do_nothing()

Example of multiple commands:
buy_crypto_price("BTC", 1000, "Strong bullish momentum")
sell_crypto_limit("ETH", 500, "Taking profits at resistance", 2250)
cancel_order(123)

IMPORTANT: Each command must be on a new line and include a summary string in quotes for trades.
"""

    def get_advice(self, market_data, portfolio_data, technical_analysis):
        current_time = datetime.now().isoformat()
        
        # Log the input data
        logging.info("=== AI Trading Analysis Start ===")
        logging.info(f"Time: {current_time}")
        logging.info(f"Portfolio Balance: ${portfolio_data['balance']:.2f}")
        logging.info("Current Positions:")
        for position in portfolio_data['positions']:
            logging.info(f"  {position['symbol']}: {position['quantity']:.8f} units")
        
        # Construct the full prompt with current data
        full_prompt = self.base_prompt.format(current_time=current_time)
        data_prompt = f"""
Current Market Data: {market_data}
Technical Analysis: {technical_analysis}
Portfolio Status: {portfolio_data}
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
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
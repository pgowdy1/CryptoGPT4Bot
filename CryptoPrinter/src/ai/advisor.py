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
You have access to real-time market data, technical indicators, and news.
You will be using a mock portfolio that starts with $10,000.

Key Rules and Considerations:
1. Never risk more than 15% of the total account balance on any single trade
2. Maintain a cash reserve of at least 20% to capitalize on opportunities
3. Use stop-losses to limit losses to 3% of total account balance
4. Use technical analysis and news sentiment
5. Trade only with high-confidence setups
6. Adapt to market conditions (bullish, bearish, sideways)
7. Make decisions every 15 minutes based on updated data
8. Avoid overtrading (max 10 trades per hour)

The current date and time is {current_time}.
"""

    def get_advice(self, market_data, portfolio_data, technical_analysis, news):
        current_time = datetime.now().isoformat()
        
        # Construct the full prompt with current data
        full_prompt = self.base_prompt.format(current_time=current_time)
        data_prompt = f"""
Current Market Data: {market_data}
Technical Analysis: {technical_analysis}
Portfolio Status: {portfolio_data}
News: {news}
"""

        user_prompt = """
What should we do to make the most amount of profit based on the info provided?

RESPOND WITH ONLY ONE OF THESE COMMANDS ON THE LAST LINE OF YOUR RESPONSE:
buy_crypto_price("symbol", amount, "single summary string")
buy_crypto_limit("symbol", amount, "single summary string", limit)
sell_crypto_price("symbol", amount, "single summary string")
sell_crypto_limit("symbol", amount, "single summary string", limit)
cancel_order(orderId)
do_nothing()

IMPORTANT: The summary must be a single string in quotes, not multiple comma-separated strings.
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": full_prompt + data_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
            )
            return response.choices[0].message.content
        except Exception as e:
            logging.error(f"Error getting AI advice: {e}")
            return None
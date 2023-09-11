from flask import Flask, request, jsonify
import ccxt
import time
import datetime

app = Flask(__name__)

# Replace with your API keys
binance_api_key = '6x1UJCQx8BKaZmdDdrm7RhF49gGKljmrpDgX5x9Q7scPsiKzF4rOGX22spGQRb0Q'
binance_secret_key = 'XeKckI6pBQoKHTVtFK3ZAQNgOCtaQsE3llAMkbojr86auJKDXOABXuFFgTaxLKZF'
bitfinex_api_key = 'k4nTkEikYlN2WrnR7QWYr1S6yg6rlY6CsdyvIFIHp8a'
bitfinex_secret_key = '214aQmFAPEa9DMf6vDayDFtCmudRrAIvQUQwfrRFvR9'

# Initialize Binance and Bitfinex exchanges
binance = ccxt.binance({'apiKey': binance_api_key, 'secret': binance_secret_key})
bitfinex = ccxt.bitfinex({'apiKey': bitfinex_api_key, 'secret': bitfinex_secret_key})

# Define trading parameters
trading_pair = 'BTCUSDT'
stop_loss_percentage = 2
take_profit_percentage = 5
trailing_stop_percentage = 1
trailing_stop_update_percentage = 0.5
trailing_stop_reset_percentage = 0.2
trailing_stop_cooldown = 300
minimum_price_difference = 10

# Function to place a buy order
def place_buy_order(exchange, symbol, quantity, price):
    try:
        order = exchange.create_limit_buy_order(symbol, quantity, price)
        return order
    except Exception as e:
        print('Error placing buy order:', e)
        return None

# Function to place a sell order
def place_sell_order(exchange, symbol, quantity, price):
    try:
        order = exchange.create_limit_sell_order(symbol, quantity, price)
        return order
    except Exception as e:
        print('Error placing sell order:', e)
        return None

# Function to calculate take-profit price
def calculate_take_profit_price(buy_price, take_profit_percentage):
    return buy_price * (1 + take_profit_percentage / 100)

# Function to calculate stop-loss price
def calculate_stop_loss_price(buy_price, stop_loss_percentage):
    return buy_price * (1 - stop_loss_percentage / 100)

# Function to implement trailing stop
def trailing_stop(exchange, symbol, quantity, buy_price, trailing_stop_percentage, minimum_price_difference):
    try:
        trailing_stop_price = buy_price * (1 - trailing_stop_percentage / 100)
        current_price = exchange.fetch_ticker(symbol)['last']
        while current_price >= trailing_stop_price:
            current_price = exchange.fetch_ticker(symbol)['last']
            trailing_stop_price = current_price * (1 - trailing_stop_percentage / 100)
            time.sleep(5)
        
        # Check if trailing stop was triggered due to minimum price difference
        if buy_price - trailing_stop_price >= minimum_price_difference:
            print(f'Trailing stop triggered! Selling at {trailing_stop_price}')
            place_sell_order(exchange, symbol, quantity, trailing_stop_price)
    except Exception as e:
        print('Error with trailing stop:', e)

# Route to stop the bot
@app.route('/stop-bot', methods=['POST'])
def stop_bot():
    try:
        # Implement the logic to stop the bot here
        # For example:
        # - Cancel open orders on both exchanges
        binance.cancel_all_orders(trading_pair)
        bitfinex.cancel_all_orders(trading_pair)
        
        # - Close any active positions on both exchanges
        binance.close_positions(trading_pair)
        bitfinex.close_positions(trading_pair)

        response_data = {
            'success': True,
            'message': 'Bot stopped successfully'
        }
    except Exception as e:
        response_data = {
            'success': False,
            'message': f'Error stopping the bot: {str(e)}'
        }

    return jsonify(response_data)

# Main trading loop
while True:
    try:
        # Place a buy order on Binance
        buy_price = binance.fetch_order_book(trading_pair)['asks'][0][0]
        buy_quantity = 0.001  # Replace with the desired quantity
        buy_order = place_buy_order(binance, trading_pair, buy_quantity, buy_price)
        
        if buy_order:
            print('Buy order placed successfully:', buy_order)

            # Calculate take-profit and stop-loss prices
            take_profit_price = calculate_take_profit_price(buy_price, take_profit_percentage)
            stop_loss_price = calculate_stop_loss_price(buy_price, stop_loss_percentage)

            # Place a sell order on Bitfinex
            sell_quantity = buy_quantity  # Replace with the desired quantity
            sell_order = place_sell_order(bitfinex, trading_pair, sell_quantity, buy_price)

            if sell_order:
                print('Sell order placed successfully:', sell_order)

                # Implement trailing stop
                trailing_stop(bitfinex, trading_pair, sell_quantity, buy_price, trailing_stop_percentage, minimum_price_difference)
    
    except Exception as e:
        print('Error:', e)

    time.sleep(5)

if __name__ == '__main__':
    app.run(debug=True)

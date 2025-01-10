import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
import time

# Initialize MetaTrader 5
if not mt5.initialize():
    print("Failed to initialize MT5")
    quit()

# Define trading parameters
symbol = "GOLD"  # Replace with your broker's symbol for gold
lot_size = 0.15   # Volume of the trade
sl_pips = 100     # Stop Loss distance in pips
tp_pips = 200     # Take Profit distance in pips
profit_target = 100  # Profit target in account currency (e.g., $50)
loss_target = -10  # Loss target in account currency (e.g., -$20)

# Track cumulative profit and loss
cumulative_profit_loss = 0.5

# Helper functions
def fetch_symbol_data(symbol, timeframe=mt5.TIMEFRAME_M1, count=100):
    """Fetch historical data for the symbol."""
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
    if rates is None:
        print(f"Failed to fetch data for {symbol}. Error: {mt5.last_error()}")
        return pd.DataFrame()
    data = pd.DataFrame(rates)
    data['time'] = pd.to_datetime(data['time'], unit='s')
    return data

def place_trade(symbol, action, lot=0.1, sl_pips=None, tp_pips=None):
    """Place a trade and manage risk with Stop Loss (SL) and Take Profit (TP)."""
    # Get the current price
    symbol_info = mt5.symbol_info_tick(symbol)
    if action == "BUY":
        order_type = mt5.ORDER_TYPE_BUY
        price = symbol_info.ask
        sl_price = price - (sl_pips * mt5.symbol_info(symbol).point) if sl_pips else 0.0
        tp_price = price + (tp_pips * mt5.symbol_info(symbol).point) if tp_pips else 0.0
    elif action == "SELL":
        order_type = mt5.ORDER_TYPE_SELL
        price = symbol_info.bid
        sl_price = price + (sl_pips * mt5.symbol_info(symbol).point) if sl_pips else 0.0
        tp_price = price - (tp_pips * mt5.symbol_info(symbol).point) if tp_pips else 0.0
    else:
        print("Invalid action. Must be 'BUY' or 'SELL'.")
        return

    # Prepare trade request
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": order_type,
        "price": price,
        "deviation": 10,
        "sl": sl_price,
        "tp": tp_price,
        "magic": 123456,
        "comment": "Python Bot",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    # Send order
    result = mt5.order_send(request)
    print(f"Order result: {result}")
    return result

def check_profit_loss():
    """Calculate the total profit/loss for the current session."""
    global cumulative_profit_loss
    account_info = mt5.account_info()
    if account_info is None:
        print("Failed to fetch account info.")
        return

    profit_loss = account_info.profit
    cumulative_profit_loss = profit_loss
    print(f"Cumulative Profit/Loss: {cumulative_profit_loss}")

    # Stop trading if profit or loss target is reached
    if cumulative_profit_loss >= profit_target:
        print(f"Profit target of {profit_target} reached. Stopping trading.")
        return True
    if cumulative_profit_loss <= loss_target:
        print(f"Loss target of {loss_target} reached. Stopping trading.")
        return True
    return False

# Trading bot logic
def trading_bot():
    # Check profit and loss before trading
    if check_profit_loss():
        mt5.shutdown()
        quit()

    # Fetch the latest data
    data = fetch_symbol_data(symbol)
    if data.empty:
        print("No data fetched for analysis.")
        return

    # Example simple strategy: Buy if last close is higher than the previous close
    if data['close'].iloc[-1] > data['close'].iloc[-2]:
        print("Condition met: Placing BUY order")
        place_trade(symbol, "BUY", lot=lot_size, sl_pips=sl_pips, tp_pips=tp_pips)
    else:
        print("Condition not met: No trade executed.")

# Run the bot
while True:
    trading_bot()
    time.sleep(30)  # Wait 60 seconds before running the bot again

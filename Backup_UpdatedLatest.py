import pandas as pd
import numpy as np
import pandas_ta as ta
import pendulum as dt
import os
import sys
import certifi
import pytz
import time
import webbrowser
import pickle
from fyers_apiv3 import fyersModel
from fyers_apiv3.FyersWebsocket import data_ws

# Globals and configuration
client_id = 'V9GQM61IVI-100'  # Replace with your client ID
secret_key = '3OH8C9ELBB'  # Replace with your secret key
redirect_uri = 'https://127.0.0.1:5000/login'
strategy_name = 'nifty_supertrend_option_selling'

index_name = 'NIFTY50'
exchange = 'NSE'
ticker = f"{exchange}:{index_name}-INDEX"
strike_count = 10
strike_diff = 50
# Trading mode - 'PAPER' for simulation, 'LIVE' for real trading
account_type = 'PAPER'  # Change to 'LIVE' when ready to place real orders
quantity = 75

if exchange == 'NSE':
    time_zone = "Asia/Kolkata"

# Trading hours
start_hour, start_min = 9, 16
end_hour, end_min = 15, 18

# Strategy parameters
supertrend_period = 10
supertrend_multiplier = 3.5
ema_period = 20

# For SSL certification on Windows
os.environ['SSL_CERT_FILE'] = certifi.where()

# Configure logging
import logging
logging.basicConfig(level=logging.INFO, 
                    filename=f'{strategy_name}_{dt.now(time_zone).date()}.log',
                    filemode='a',
                    format="%(asctime)s - %(message)s")

def get_access_token():
    """Get access token from file or generate new one"""
    if os.path.exists(f'access-{dt.now(time_zone).date()}.txt'):
        print('Access token exists')
        with open(f'access-{dt.now(time_zone).date()}.txt', 'r') as f:
            access_token = f.read()
    else:
        # Define response type and state for the session
        response_type = "code"
        state = "sample_state"
        try:
            # Create a session model with the provided credentials
            session = fyersModel.SessionModel(
                client_id=client_id,
                secret_key=secret_key,
                redirect_uri=redirect_uri,
                response_type=response_type
            )

            # Generate the auth code using the session model
            response = session.generate_authcode()
            print(response)

            # Open the auth code URL in a new browser window
            webbrowser.open(response, new=1)
            newurl = input("Enter the url: ")
            auth_code = newurl[newurl.index('auth_code=')+10:newurl.index('&state')]

            # Define grant type for the session
            grant_type = "authorization_code"
            session = fyersModel.SessionModel(
                client_id=client_id,
                secret_key=secret_key,
                redirect_uri=redirect_uri,
                response_type=response_type,
                grant_type=grant_type
            )

            # Set the authorization code in the session object
            session.set_token(auth_code)

            # Generate the access token using the authorization code
            response = session.generate_token()

            # Save the access token to access.txt
            access_token = response["access_token"]
            with open(f'access-{dt.now(time_zone).date()}.txt', 'w') as k:
                k.write(access_token)
        except Exception as e:
            print(e, response)
            print('Unable to get access token')
            sys.exit()
    
    print('Access token:', access_token)
    return access_token

def initialize_fyers(access_token):
    """Initialize FyersModel instance"""
    fyers = fyersModel.FyersModel(client_id=client_id, is_async=False, token=access_token, log_path=None)
    return fyers

def get_current_expiry(fyers, ticker, strike_count):
    """Get the current expiry dates from option chain"""
    # Define the data for the option chain request
    data = {
        "symbol": ticker,
        "strikecount": strike_count,
        "timestamp": ""
    }
    
    # Get the expiry data from the option chain
    response = fyers.optionchain(data=data)['data']
    
    # Get all available expiry dates
    expiry_dates = []
    for expiry_item in response['expiryData']:
        expiry_dates.append({
            'date': expiry_item['date'],
            'expiry': expiry_item['expiry']
        })
    
    return expiry_dates

def get_option_chain(fyers, ticker, strike_count, expiry_timestamp):
    """Get option chain data for a specific expiry"""
    data = {
        "symbol": ticker,
        "strikecount": strike_count,
        "timestamp": expiry_timestamp
    }
    
    # Get the option chain data
    response = fyers.optionchain(data=data)['data']
    option_chain = pd.DataFrame(response['optionsChain'])
    
    # Get the spot price
    spot_price = option_chain['ltp'].iloc[0]
    
    return option_chain, spot_price

def calculate_supertrend(df, period=10, multiplier=3):
    # Calculate ATR
    high = df['high']
    low = df['low']
    close = df['close']
    
    tr1 = pd.DataFrame(high - low)
    tr2 = pd.DataFrame(abs(high - close.shift(1)))
    tr3 = pd.DataFrame(abs(low - close.shift(1)))
    frames = [tr1, tr2, tr3]
    tr = pd.concat(frames, axis=1, join='inner').max(axis=1)
    atr = tr.ewm(alpha=1/period).mean()

    # Calculate Basic Upper and Lower Bands
    basic_upper = (high + low) / 2 + (multiplier * atr)
    basic_lower = (high + low) / 2 - (multiplier * atr)

    # Initialize Final Upper and Lower Bands
    final_upper = basic_upper.copy()
    final_lower = basic_lower.copy()
    
    for i in range(1, len(df)):
        if (basic_upper.iloc[i] < final_upper.iloc[i-1] and 
            close.iloc[i-1] <= final_upper.iloc[i-1]):
            final_upper.iloc[i] = basic_upper.iloc[i]
        elif (basic_upper.iloc[i] > final_upper.iloc[i-1] and 
              close.iloc[i-1] <= final_upper.iloc[i-1]):
            final_upper.iloc[i] = final_upper.iloc[i-1]
        elif (basic_upper.iloc[i] < final_upper.iloc[i-1] and 
              close.iloc[i-1] > final_upper.iloc[i-1]):
            final_upper.iloc[i] = basic_upper.iloc[i]
        elif (basic_upper.iloc[i] > final_upper.iloc[i-1] and 
              close.iloc[i-1] > final_upper.iloc[i-1]):
            final_upper.iloc[i] = basic_upper.iloc[i]

        if (basic_lower.iloc[i] > final_lower.iloc[i-1] and 
            close.iloc[i-1] >= final_lower.iloc[i-1]):
            final_lower.iloc[i] = basic_lower.iloc[i]
        elif (basic_lower.iloc[i] < final_lower.iloc[i-1] and 
              close.iloc[i-1] >= final_lower.iloc[i-1]):
            final_lower.iloc[i] = final_lower.iloc[i-1]
        elif (basic_lower.iloc[i] > final_lower.iloc[i-1] and 
              close.iloc[i-1] < final_lower.iloc[i-1]):
            final_lower.iloc[i] = basic_lower.iloc[i]
        elif (basic_lower.iloc[i] < final_lower.iloc[i-1] and 
              close.iloc[i-1] < final_lower.iloc[i-1]):
            final_lower.iloc[i] = basic_lower.iloc[i]

    # Calculate Supertrend and Direction
    supertrend = pd.Series(index=df.index, dtype=float)
    supertrend_direction = pd.Series(index=df.index, dtype=int)

    for i in range(len(df)):
        if i == 0:
            supertrend.iloc[i] = final_upper.iloc[i]
            supertrend_direction.iloc[i] = 1
        else:
            if (supertrend.iloc[i-1] == final_upper.iloc[i-1] and 
                close.iloc[i] <= final_upper.iloc[i]):
                supertrend.iloc[i] = final_upper.iloc[i]
                supertrend_direction.iloc[i] = -1
            elif (supertrend.iloc[i-1] == final_upper.iloc[i-1] and 
                  close.iloc[i] > final_upper.iloc[i]):
                supertrend.iloc[i] = final_lower.iloc[i]
                supertrend_direction.iloc[i] = 1
            elif (supertrend.iloc[i-1] == final_lower.iloc[i-1] and 
                  close.iloc[i] >= final_lower.iloc[i]):
                supertrend.iloc[i] = final_lower.iloc[i]
                supertrend_direction.iloc[i] = 1
            elif (supertrend.iloc[i-1] == final_lower.iloc[i-1] and 
                  close.iloc[i] < final_lower.iloc[i]):
                supertrend.iloc[i] = final_upper.iloc[i]
                supertrend_direction.iloc[i] = -1

    # Add the calculated columns to the dataframe
    df['basic_upper'] = basic_upper
    df['basic_lower'] = basic_lower
    df['supertrend_upper'] = final_upper
    df['supertrend_lower'] = final_lower
    df['supertrend'] = supertrend
    df['supertrend_direction'] = supertrend_direction
    
    return df

def calculate_ema(df, period=20):
    """Calculate Exponential Moving Average"""
    df['ema'] = df['close'].ewm(span=period, adjust=False).mean()
    return df

def get_historical_data(fyers, ticker, interval='1D', days=10):
    """Fetch historical data for the given ticker"""
    from_date = dt.now(time_zone).date() - dt.duration(days=days)
    to_date = dt.now(time_zone).date()
    
    data = {
        "symbol": ticker,
        "resolution": interval,
        "date_format": "1",
        "range_from": from_date.strftime('%Y-%m-%d'),
        "range_to": to_date.strftime('%Y-%m-%d'),
        "cont_flag": "1"
    }
    
    # Fetch historical data
    response = fyers.history(data=data)
    
    if response['s'] == 'ok':
        hist_data = pd.DataFrame(response['candles'])
        hist_data.columns = ['date', 'open', 'high', 'low', 'close', 'volume']
        ist = pytz.timezone('Asia/Kolkata')
        hist_data['date'] = pd.to_datetime(hist_data['date'], unit='s').dt.tz_localize('UTC').dt.tz_convert(ist)
        hist_data.set_index('date', inplace=True)
        return hist_data
    else:
        print(f"Error fetching historical data: {response['message']}")
        return pd.DataFrame()

def calculate_option_delta(S, K, T, r, sigma, option_type='CE'):
    """
    Calculate option delta using Black-Scholes model
    
    Parameters:
    -----------
    S : float
        Current spot price of the underlying
    K : float
        Strike price of the option
    T : float
        Time to expiration in years
    r : float
        Risk-free interest rate (annual)
    sigma : float
        Implied volatility of the underlying
    option_type : str
        'CE' for call option, 'PE' for put option
        
    Returns:
    --------
    float: The delta value of the option
    """
    from scipy.stats import norm
    import numpy as np
    
    # Convert to Black-Scholes notation
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    
    if option_type == 'CE':
        delta = norm.cdf(d1)
    else:  # 'PE'
        delta = -norm.cdf(-d1)
        
    return delta

def calculate_implied_volatility(option_chain, expiry_date, spot_price, nifty_hist_data=None):
    """
    Calculate implied volatility for the option chain
    
    If nifty_hist_data is provided, historical volatility will be used as a starting point.
    Otherwise, a default value will be used.
    """
    import numpy as np
    from datetime import datetime
    
    # Default implied volatility (annualized)
    default_iv = 0.20  # 20% implied volatility
    
    # Calculate historical volatility if historical data is provided
    if nifty_hist_data is not None:
        # Calculate daily returns
        nifty_hist_data['returns'] = nifty_hist_data['close'].pct_change()
        
        # Calculate 30-day historical volatility (annualized)
        hist_vol = nifty_hist_data['returns'].tail(30).std() * np.sqrt(252)
        
        # Use historical volatility with a small adjustment
        iv = max(hist_vol, 0.15)  # Floor of 15%
    else:
        iv = default_iv
    
    # Calculate days to expiry
    current_date = dt.now(time_zone).date()
    
    # Handle different date formats that might be in expiry_date
    if isinstance(expiry_date, dict) and 'date' in expiry_date:
        expiry_str = expiry_date['date']
        # Try different date formats
        try:
            # Try standard datetime parsing
            expiry_datetime = datetime.strptime(expiry_str, '%d-%m-%Y')
        except ValueError:
            try:
                # Try another common format
                expiry_datetime = datetime.strptime(expiry_str, '%Y-%m-%d')
            except ValueError:
                # If all else fails, use a default expiry (7 days from now)
                logging.warning(f"Could not parse expiry date {expiry_str}, using default 7 days")
                expiry_datetime = dt.now(time_zone).add(days=7)
    else:
        # If expiry_date is not as expected, use a default
        logging.warning("Invalid expiry_date format, using default 7 days")
        expiry_datetime = dt.now(time_zone).add(days=7)
    
    # Convert to date object if it's a datetime
    if hasattr(expiry_datetime, 'date'):
        expiry_date_obj = expiry_datetime.date()
    else:
        expiry_date_obj = expiry_datetime
    
    days_to_expiry = (expiry_date_obj - current_date).days + 1
    days_to_expiry = max(days_to_expiry, 1)  # Ensure at least 1 day
    
    # Convert to years
    T = days_to_expiry / 365
    
    return iv, T

def get_option_by_delta(option_chain, spot_price, delta_target, option_type, expiry_date):
    """Find option with delta closest to target"""
    # Get risk-free rate (1-year T-bill rate or similar)
    risk_free_rate = 0.06  # 6% approximate risk-free rate for INR
    
    # Calculate implied volatility and time to expiry
    iv, T = calculate_implied_volatility(option_chain, expiry_date, spot_price)
    
    # Filter by option type
    filtered_chain = option_chain[option_chain['option_type'] == option_type]
    
    # Calculate delta for each option
    deltas = []
    
    for index, row in filtered_chain.iterrows():
        strike = row['strike_price']
        delta = calculate_option_delta(
            S=spot_price,
            K=strike,
            T=T,
            r=risk_free_rate,
            sigma=iv,
            option_type=option_type
        )
        deltas.append((index, delta))
    
    # Find option with delta closest to target
    closest_index, closest_delta = min(deltas, key=lambda x: abs(x[1] - delta_target))
    
    option = filtered_chain.loc[closest_index].copy()
    option['calculated_delta'] = closest_delta
    
    return option

def select_expiry_based_on_day(expiry_dates, current_date):
    """Select appropriate expiry based on the day of the week"""
    weekday = current_date.weekday()  # 0 = Monday, 1 = Tuesday, ..., 6 = Sunday
    
    # Logic based on requirements:
    # Mon-Thu: Use next week expiry
    # Fri: Use current week expiry
    if weekday < 4:  # Monday to Thursday
        if len(expiry_dates) > 1:
            return expiry_dates[1]  # Next expiry
        return expiry_dates[0]  # If only one expiry available
    else:  # Friday
        return expiry_dates[0]  # Current week expiry

def check_exit_before_expiry(current_time, expiry_date):
    """Check if we need to exit positions before expiry (16 min before)"""
    try:
        # Handle different date formats
        if isinstance(expiry_date, dict) and 'date' in expiry_date:
            expiry_str = expiry_date['date']
            # Try different date formats
            try:
                # Try DD-MM-YYYY format
                expiry_dt = dt.from_format(expiry_str, 'DD-MM-YYYY')
            except:
                try:
                    # Try YYYY-MM-DD format
                    expiry_dt = dt.from_format(expiry_str, 'YYYY-MM-DD')
                except:
                    try:
                        # Try [DD-MM-YYYY] format (remove brackets)
                        clean_str = expiry_str.strip('[]')
                        expiry_dt = dt.from_format(clean_str, 'DD-MM-YYYY')
                    except:
                        logging.error(f"Could not parse expiry date string: {expiry_str}")
                        return False

        else:
            logging.error(f"Invalid expiry_date format: {expiry_date}")
            return False

        # Set the expiry time to 15:30 IST
        expiry_dt = expiry_dt.set(hour=15, minute=30)
        
        # Get time 16 minutes before expiry
        exit_time = expiry_dt.subtract(minutes=16)
        
        return current_time >= exit_time

    except Exception as e:
        logging.error(f"Error in check_exit_before_expiry: {e}")
        return False

def store_trading_data(data, account_type):
    """Store trading data using pickle"""
    filename = f'data-{account_type}.pickle'
    with open(filename, 'wb') as f:
        pickle.dump(data, f)

def load_trading_data(account_type):
    """Load trading data using pickle"""
    filename = f'data-{account_type}.pickle'
    try:
        with open(filename, 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        logging.info(f"No existing trading data found for {filename}")
        return None
    except Exception as e:
        logging.error(f"Error loading trading data: {e}")
        return None

def get_current_option_price(fyers, symbol):
    """Get current market price for an option symbol"""
    try:
        # Get current market data for the symbol
        data = {"symbols": symbol}
        response = fyers.quotes(data=data)
        
        if response['s'] == 'ok' and 'd' in response:
            # Return the LTP (Last Traded Price)
            return response['d'][0]['v']['lp']
        else:
            logging.warning(f"Could not get price for {symbol}: {response}")
            return 0
    except Exception as e:
        logging.error(f"Error getting current price for {symbol}: {e}")
        return 0

def log_trade_pair(trading_state, leg1_data, leg2_data, spot_price, trade_type="Entry", reason="Strategy"):
    """Log both legs of a strategy with proper timestamps"""
    base_time = dt.now(time_zone)
    
    # Log first leg
    trading_state['trades'].loc[base_time] = [
        leg1_data['symbol'], 
        leg1_data['price'], 
        leg1_data['action'], 
        f"{trade_type} - {reason} - {leg1_data['leg_type']}", 
        spot_price
    ]
    
    # Log second leg with microsecond offset to avoid overwriting
    trading_state['trades'].loc[base_time.add(microseconds=1)] = [
        leg2_data['symbol'], 
        leg2_data['price'], 
        leg2_data['action'], 
        f"{trade_type} - {reason} - {leg2_data['leg_type']}", 
        spot_price
    ]
    
    logging.info(f"{trade_type}: {leg1_data['leg_type']} {leg1_data['symbol']} @ {leg1_data['price']}, "
                f"{leg2_data['leg_type']} {leg2_data['symbol']} @ {leg2_data['price']}")

def place_order(fyers, symbol, action, quantity, limit_price=0):
    """Place an order in the market
    
    Args:
        fyers: FyersModel instance
        symbol: Trading symbol
        action: 1 for buy, -1 for sell
        quantity: Number of units to trade
        limit_price: Price for limit order, 0 for market order
    """
    # Check if we're in paper trading mode
    if account_type == 'PAPER':
        # Log the order details but don't actually place the order
        order_type = "Limit" if limit_price > 0 else "Market"
        action_str = "BUY" if action == 1 else "SELL"
        logging.info(f"PAPER TRADE: {action_str} {quantity} {symbol} @ {limit_price if limit_price > 0 else 'MARKET'}")
        
        # Simulate a successful order response
        return {"s": "ok", "message": "Paper trading order simulated", "orderNumber": f"PAPER-{int(time.time())}"}
    
    # If not in paper trading mode, place a real order
    order_type = 2  # Market order
    if limit_price > 0:
        order_type = 1  # Limit order
    
    try:
        data = {
            "symbol": symbol,
            "qty": quantity,
            "type": order_type,
            "side": action,
            "productType": "MARGIN",
            "limitPrice": limit_price,
            "stopPrice": 0,
            "validity": "DAY",
            "disclosedQty": 0,
            "offlineOrder": False,
            "stopLoss": 0,
            "takeProfit": 0
        }
        response = fyers.place_order(data=data)
        logging.info(f"LIVE TRADE: Order placed: {symbol}, {action}, {quantity}, {limit_price}. Response: {response}")
        return response
    except Exception as e:
        logging.error(f"Error placing order: {e}")
        return {"s": "error", "message": str(e)}

def enhanced_exit_position(fyers, symbol, account_type):
    """Exit position and return the exit price"""
    if account_type == 'PAPER':
        # For paper trading, get current market price
        exit_price = get_current_option_price(fyers, symbol)
        logging.info(f"PAPER TRADE: Exiting position for {symbol} @ {exit_price}")
        return {"s": "ok", "message": "Paper trading position exit simulated", "exit_price": exit_price}
    
    # For live trading, first get current price, then exit
    exit_price = get_current_option_price(fyers, symbol)
    
    try:
        data = {"id": symbol + "-MARGIN"}
        response = fyers.exit_positions(data=data)
        response["exit_price"] = exit_price  # Add exit price to response
        logging.info(f"LIVE TRADE: Exited position: {symbol} @ {exit_price}. Response: {response}")
        return response
    except Exception as e:
        logging.error(f"Error exiting position: {e}")
        return {"s": "error", "message": str(e), "exit_price": 0}

def execute_long_entry(fyers, trading_state, option_chain, spot_price, selected_expiry, quantity, account_type):
    """Execute long position entry with proper logging"""
    try:
        # Find options
        sell_put = get_option_by_delta(option_chain, spot_price, -0.4, 'PE', selected_expiry)
        buy_put = get_option_by_delta(option_chain, spot_price, -0.25, 'PE', selected_expiry)
        
        logging.info(f"Selected put to sell: {sell_put['symbol']} with delta ~{sell_put.get('calculated_delta', '?')}")
        logging.info(f"Selected put to buy: {buy_put['symbol']} with delta ~{buy_put.get('calculated_delta', '?')}")
        
        # Place orders
        buy_order_result = place_order(fyers, buy_put['symbol'], 1, quantity)
        sell_order_result = place_order(fyers, sell_put['symbol'], -1, quantity)
        
        if sell_order_result.get('s') == 'ok' and buy_order_result.get('s') == 'ok':
            # Update trading state
            trading_state['position'] = 'long'
            trading_state['entry_time'] = dt.now(time_zone)
            trading_state['entry_price'] = spot_price
            trading_state['sell_put_symbol'] = sell_put['symbol']
            trading_state['buy_put_symbol'] = buy_put['symbol']
            trading_state['expiry'] = selected_expiry
            
            # Log both trades properly
            leg1_data = {
                'symbol': sell_put['symbol'],
                'price': sell_put['ltp'],
                'action': -1,
                'leg_type': 'Sell Put'
            }
            leg2_data = {
                'symbol': buy_put['symbol'],
                'price': buy_put['ltp'],
                'action': 1,
                'leg_type': 'Buy Put'
            }
            
            log_trade_pair(trading_state, leg1_data, leg2_data, spot_price, "Entry", "Long Put Spread")
            return True
        else:
            logging.error(f"Failed to place long orders: Sell={sell_order_result}, Buy={buy_order_result}")
            return False
            
    except Exception as e:
        logging.error(f"Error in long entry: {e}")
        return False

def execute_short_entry(fyers, trading_state, option_chain, spot_price, selected_expiry, quantity, account_type):
    """Execute short position entry with proper logging"""
    try:
        # Find options
        sell_call = get_option_by_delta(option_chain, spot_price, 0.4, 'CE', selected_expiry)
        buy_call = get_option_by_delta(option_chain, spot_price, 0.25, 'CE', selected_expiry)
        
        logging.info(f"Selected call to sell: {sell_call['symbol']} with delta ~{sell_call.get('calculated_delta', '?')}")
        logging.info(f"Selected call to buy: {buy_call['symbol']} with delta ~{buy_call.get('calculated_delta', '?')}")
        
        # Place orders
        buy_order_result = place_order(fyers, buy_call['symbol'], 1, quantity)
        sell_order_result = place_order(fyers, sell_call['symbol'], -1, quantity)
        
        if sell_order_result.get('s') == 'ok' and buy_order_result.get('s') == 'ok':
            # Update trading state
            trading_state['position'] = 'short'
            trading_state['entry_time'] = dt.now(time_zone)
            trading_state['entry_price'] = spot_price
            trading_state['sell_call_symbol'] = sell_call['symbol']
            trading_state['buy_call_symbol'] = buy_call['symbol']
            trading_state['expiry'] = selected_expiry
            
            # Log both trades properly
            leg1_data = {
                'symbol': sell_call['symbol'],
                'price': sell_call['ltp'],
                'action': -1,
                'leg_type': 'Sell Call'
            }
            leg2_data = {
                'symbol': buy_call['symbol'],
                'price': buy_call['ltp'],
                'action': 1,
                'leg_type': 'Buy Call'
            }
            
            log_trade_pair(trading_state, leg1_data, leg2_data, spot_price, "Entry", "Short Call Spread")
            return True
        else:
            logging.error(f"Failed to place short orders: Sell={sell_order_result}, Buy={buy_order_result}")
            return False
            
    except Exception as e:
        logging.error(f"Error in short entry: {e}")
        return False

def execute_position_exit(fyers, trading_state, spot_price, reason, account_type):
    """Execute position exit with proper price logging"""
    try:
        if trading_state['position'] == 'long':
            # Exit long position - get actual exit prices
            sell_put_exit = enhanced_exit_position(fyers, trading_state['sell_put_symbol'], account_type)
            buy_put_exit = enhanced_exit_position(fyers, trading_state['buy_put_symbol'], account_type)
            
            if sell_put_exit.get('s') == 'ok' and buy_put_exit.get('s') == 'ok':
                # Log both exits with actual prices
                leg1_data = {
                    'symbol': trading_state['sell_put_symbol'],
                    'price': sell_put_exit.get('exit_price', 0),
                    'action': 1,  # Buying back the sold put
                    'leg_type': 'Buy Back Put'
                }
                leg2_data = {
                    'symbol': trading_state['buy_put_symbol'],
                    'price': buy_put_exit.get('exit_price', 0),
                    'action': -1,  # Selling the bought put
                    'leg_type': 'Sell Put'
                }
                
                log_trade_pair(trading_state, leg1_data, leg2_data, spot_price, "Exit", reason)
                
                # Reset position
                trading_state['position'] = None
                trading_state['entry_time'] = None
                trading_state['entry_price'] = 0
                trading_state['sell_put_symbol'] = ''
                trading_state['buy_put_symbol'] = ''
                trading_state['expiry'] = None
                
                return True
            else:
                logging.error(f"Failed to exit long position: SellPut={sell_put_exit}, BuyPut={buy_put_exit}")
                return False
                
        elif trading_state['position'] == 'short':
            # Exit short position - get actual exit prices
            sell_call_exit = enhanced_exit_position(fyers, trading_state['sell_call_symbol'], account_type)
            buy_call_exit = enhanced_exit_position(fyers, trading_state['buy_call_symbol'], account_type)
            
            if sell_call_exit.get('s') == 'ok' and buy_call_exit.get('s') == 'ok':
                # Log both exits with actual prices
                leg1_data = {
                    'symbol': trading_state['sell_call_symbol'],
                    'price': sell_call_exit.get('exit_price', 0),
                    'action': 1,  # Buying back the sold call
                    'leg_type': 'Buy Back Call'
                }
                leg2_data = {
                    'symbol': trading_state['buy_call_symbol'],
                    'price': buy_call_exit.get('exit_price', 0),
                    'action': -1,  # Selling the bought call
                    'leg_type': 'Sell Call'
                }
                
                log_trade_pair(trading_state, leg1_data, leg2_data, spot_price, "Exit", reason)
                
                # Reset position
                trading_state['position'] = None
                trading_state['entry_time'] = None
                trading_state['entry_price'] = 0
                trading_state['sell_call_symbol'] = ''
                trading_state['buy_call_symbol'] = ''
                trading_state['expiry'] = None
                
                return True
            else:
                logging.error(f"Failed to exit short position: SellCall={sell_call_exit}, BuyCall={buy_call_exit}")
                return False
                
    except Exception as e:
        logging.error(f"Error during position exit: {e}")
        return False

def initialize_trading_state():
    """Initialize the trading state dictionary"""
    column_names = ['symbol', 'price', 'action', 'reason', 'spot_price']
    trades_df = pd.DataFrame(columns=column_names)
    
    state = {
        'position': None,  # 'long' or 'short' or None
        'supertrend_direction': 0,  # 1 for uptrend, -1 for downtrend
        'above_ema': False,  # True if price is above EMA
        'entry_time': None,
        'entry_price': 0,
        'sell_put_symbol': '',
        'buy_put_symbol': '',  # For long position (buy signal)
        'sell_call_symbol': '',
        'buy_call_symbol': '',  # For short position (sell signal)
        'expiry': None,
        'trades': trades_df
    }
    
    return state

def main():
    print("Starting Nifty Option Selling Strategy")
    logging.info("Starting Nifty Option Selling Strategy")
    
    # Get access token and initialize Fyers
    access_token = get_access_token()
    fyers = initialize_fyers(access_token)
    
    # Initialize trading state
    trading_state = load_trading_data(account_type)
    if not trading_state:
        trading_state = initialize_trading_state()
    
    # Get current time and define trading session times
    current_time = dt.now(time_zone)
    start_time = dt.datetime(current_time.year, current_time.month, current_time.day, start_hour, start_min, tz=time_zone)
    end_time = dt.datetime(current_time.year, current_time.month, current_time.day, end_hour, end_min, tz=time_zone)
    
    print(f"Start time: {start_time}")
    print(f"End time: {end_time}")
    
    # If current time is before start time, wait until start time
    if current_time < start_time:
        wait_seconds = (start_time - current_time).total_seconds()
        print(f"Waiting {wait_seconds/60:.1f} minutes until trading starts at {start_time}")
        logging.info(f"Waiting {wait_seconds/60:.1f} minutes until trading starts at {start_time}")
        time.sleep((wait_seconds+ 5))
    
    # Main trading loop
    while True:
        current_time = dt.now(time_zone)
        
        # Exit if we're past end time
        if current_time > end_time + dt.duration(minutes=2):
            logging.info("Trading session ended. Positions maintained for next day.")
            break
        
        # Only trade during market hours
        if start_time <= current_time <= end_time:
            try:
                # Get historical data
                hist_data = get_historical_data(fyers, ticker, interval='60', days=18)
                hist_data = hist_data.drop_duplicates()
                
                if not hist_data.empty:
                    # Calculate indicators
                    hist_data = calculate_supertrend(hist_data, period=supertrend_period, 
                                                   multiplier=supertrend_multiplier)
                    hist_data = calculate_ema(hist_data, period=ema_period)
                    
                    # Get current expiry dates
                    expiry_dates = get_current_expiry(fyers, ticker, strike_count)
                    
                    # Select appropriate expiry based on day of week
                    selected_expiry = select_expiry_based_on_day(expiry_dates, current_time)
                    
                    # Get option chain for the selected expiry
                    option_chain, spot_price = get_option_chain(fyers, ticker, strike_count, 
                                                              selected_expiry['expiry'])
                    
                    # Get the latest data for signals
                    latest_data = hist_data.iloc[-1]
                    prev_data = hist_data.iloc[-2] if len(hist_data) > 1 else None
                    
                    # Get the current supertrend direction
                    current_supertrend_direction = latest_data['supertrend_direction']
                    
                    # Check if price is above or below EMA
                    above_ema = latest_data['close'] > latest_data['ema']
                    
                    # Detect changes in signals
                    supertrend_changed = (prev_data is not None and 
                                         prev_data['supertrend_direction'] != current_supertrend_direction)
                    
                    # Signal for buying (green supertrend and price above EMA)
                    buy_signal = (current_supertrend_direction == 1 and above_ema)
                    
                    # Signal for selling (red supertrend and price below EMA)
                    sell_signal = (current_supertrend_direction == -1 and not above_ema)
                    
                    # Exit signal for buy position (supertrend turns red)
                    exit_buy_signal = (trading_state['position'] == 'long' and 
                                      current_supertrend_direction == -1)
                    
                    # Exit signal for sell position (supertrend turns green)
                    exit_sell_signal = (trading_state['position'] == 'short' and 
                                       current_supertrend_direction == 1)
                    
                    # Check if we need to exit before expiry
                    exit_for_expiry = (trading_state['position'] is not None and 
                                      trading_state['expiry'] is not None and
                                      check_exit_before_expiry(current_time, trading_state['expiry']))
                    
                    # Log current market conditions
                    logging.info(f"Spot Price: {spot_price}, Supertrend: {'Green' if current_supertrend_direction == 1 else 'Red'}, "
                                f"{'Above' if above_ema else 'Below'} EMA")
                    
                    # Position entry and exit logic
                    if trading_state['position'] is None:
                        # Entry for buy signal
                        if buy_signal:
                            logging.info("Buy signal detected")
                            execute_long_entry(fyers, trading_state, option_chain, spot_price, selected_expiry, quantity, account_type)
                        
                        # Entry for sell signal
                        elif sell_signal:
                            logging.info("Sell signal detected")
                            execute_short_entry(fyers, trading_state, option_chain, spot_price, selected_expiry, quantity, account_type)
                                                
                    # Exit positions
                    elif exit_buy_signal or exit_sell_signal or exit_for_expiry:
                        reason = "Supertrend Signal Change"
                        if exit_for_expiry:
                            reason = "Exit Before Expiry"
                        
                        logging.info(f"Exit signal detected: {reason}")
                        execute_position_exit(fyers, trading_state, spot_price, reason, account_type)
                    
                    # Save trading state
                    store_trading_data(trading_state, account_type)
                    
                    # Save trades to CSV
                    if not trading_state['trades'].empty:
                        trading_state['trades'].to_csv(f'trades_{strategy_name}_{dt.now(time_zone).date()}.csv')
                
            except Exception as e:
                logging.error(f"Error in main loop: {e}")
                print(f"Error: {e}")
        
        # Sleep before next iteration
        #time.sleep(3600)  # Check every 1Hour
        time.sleep(60)

if __name__ == "__main__":
    main()
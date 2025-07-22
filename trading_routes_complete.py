# Add these imports at the top of your Flask app (after existing imports)
import subprocess
import threading
import json
import webbrowser
from datetime import datetime
import pendulum as dt
import os
import signal
import psutil

# Global variables for trading state
TRADING_STATE_FILE = 'trading_state.txt'
TRADING_LOG_FILE = 'trading_execution.log'

# Trading configuration (you can modify these)
CLIENT_ID = 'V9GQM61IVI-100'  # Your client ID
SECRET_KEY = '3OH8C9ELBB'     # Your secret key
REDIRECT_URI = 'https://127.0.0.1:5000/login'

def read_trading_state():
    """Read current trading state from file"""
    try:
        if os.path.exists(TRADING_STATE_FILE):
            with open(TRADING_STATE_FILE, 'r') as f:
                return json.load(f)
        else:
            return {
                'access_token': None,
                'token_date': None,
                'trading_active': False,
                'process_id': None,
                'last_started': None,
                'last_stopped': None,
                'script_status': 'stopped'
            }
    except Exception as e:
        return {
            'access_token': None,
            'token_date': None,
            'trading_active': False,
            'process_id': None,
            'last_started': None,
            'last_stopped': None,
            'script_status': 'error',
            'error': str(e)
        }

def write_trading_state(state):
    """Write trading state to file"""
    try:
        with open(TRADING_STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2, default=str)
        return True
    except Exception as e:
        return False

def log_trading_event(message):
    """Log trading events to file"""
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(TRADING_LOG_FILE, 'a') as f:
            f.write(f"{timestamp} - {message}\n")
    except:
        pass

# STEP 1: Route for Access Token Creation
@app.route('/SiddarthaDas_trading/create_token')
def create_access_token():
    """Route to create access token"""
    return render_template('create_token.html')

@app.route('/SiddarthaDas_trading/generate_token', methods=['POST'])
def generate_access_token():
    """Generate access token using Fyers API"""
    try:
        from fyers_apiv3 import fyersModel
        
        # Create session model
        session = fyersModel.SessionModel(
            client_id=CLIENT_ID,
            secret_key=SECRET_KEY,
            redirect_uri=REDIRECT_URI,
            response_type="code"
        )
        
        # Generate auth code URL
        auth_url = session.generate_authcode()
        
        return jsonify({
            'status': 'success',
            'auth_url': auth_url,
            'message': 'Please complete authentication and provide the callback URL'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error generating auth URL: {str(e)}'
        }), 500

@app.route('/SiddarthaDas_trading/save_token', methods=['POST'])
def save_access_token():
    """Save access token from callback URL"""
    try:
        data = request.get_json()
        callback_url = data.get('callback_url')
        
        if not callback_url:
            return jsonify({
                'status': 'error',
                'message': 'Callback URL is required'
            }), 400
        
        # Extract auth code from URL
        if 'auth_code=' in callback_url:
            auth_code = callback_url.split('auth_code=')[1].split('&')[0]
        else:
            return jsonify({
                'status': 'error',
                'message': 'Auth code not found in callback URL'
            }), 400
        
        # Generate access token
        from fyers_apiv3 import fyersModel
        
        session = fyersModel.SessionModel(
            client_id=CLIENT_ID,
            secret_key=SECRET_KEY,
            redirect_uri=REDIRECT_URI,
            response_type="code",
            grant_type="authorization_code"
        )
        
        session.set_token(auth_code)
        response = session.generate_token()
        
        if 'access_token' in response:
            access_token = response['access_token']
            
            # Save to state file
            state = read_trading_state()
            state['access_token'] = access_token
            state['token_date'] = datetime.now().isoformat()
            write_trading_state(state)
            
            # Also save to daily file (as your script expects)
            today = dt.now('Asia/Kolkata').date()
            with open(f'access-{today}.txt', 'w') as f:
                f.write(access_token)
            
            log_trading_event("Access token generated successfully")
            
            return jsonify({
                'status': 'success',
                'message': 'Access token saved successfully'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'Failed to generate token: {response}'
            }), 500
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error saving token: {str(e)}'
        }), 500

# STEP 2: Route to Start Trading Script
@app.route('/SiddarthaDas_trading/start_script', methods=['POST'])
def start_trading_script():
    """Start the trading script"""
    try:
        state = read_trading_state()
        
        # Check if access token exists
        if not state.get('access_token'):
            return jsonify({
                'status': 'error',
                'message': 'Access token not found. Please create token first.'
            }), 400
        
        # Check if already running
        if state.get('trading_active'):
            return jsonify({
                'status': 'warning',
                'message': 'Trading script is already running'
            })
        
        # Start the trading script as subprocess
        script_path = 'UpdatedLatest.py'  # Your trading script
        if not os.path.exists(script_path):
            return jsonify({
                'status': 'error',
                'message': f'Trading script {script_path} not found'
            }), 404
        
        # Start process
        process = subprocess.Popen(
            ['python', script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # Update state
        state['trading_active'] = True
        state['process_id'] = process.pid
        state['last_started'] = datetime.now().isoformat()
        state['script_status'] = 'running'
        write_trading_state(state)
        
        log_trading_event(f"Trading script started with PID: {process.pid}")
        
        return jsonify({
            'status': 'success',
            'message': f'Trading script started successfully with PID: {process.pid}'
        })
        
    except Exception as e:
        log_trading_event(f"Error starting script: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error starting trading script: {str(e)}'
        }), 500

# STEP 3: Dashboard Route
@app.route('/SiddarthaDas_trading/dashboard')
def trading_dashboard():
    """Main trading dashboard"""
    state = read_trading_state()
    
    # Read recent logs
    recent_logs = []
    try:
        if os.path.exists(TRADING_LOG_FILE):
            with open(TRADING_LOG_FILE, 'r') as f:
                lines = f.readlines()
                recent_logs = lines[-20:]  # Last 20 lines
                recent_logs.reverse()  # Most recent first
    except:
        recent_logs = ['No logs available']
    
    # Check if process is actually running
    if state.get('process_id'):
        try:
            process = psutil.Process(state['process_id'])
            if process.is_running():
                state['script_status'] = 'running'
            else:
                state['script_status'] = 'stopped'
                state['trading_active'] = False
        except:
            state['script_status'] = 'stopped'
            state['trading_active'] = False
    
    # Get CSV files for reports
    csv_files = []
    for file in os.listdir('.'):
        if file.startswith('trades_nifty_supertrend_option_selling_') and file.endswith('.csv'):
            csv_files.append(file)
    
    return render_template('trading_dashboard.html', 
                         state=state, 
                         recent_logs=recent_logs,
                         csv_files=csv_files)

# STEP 4: Route to Stop Trading Script
@app.route('/SiddarthaDas_trading/stop_script', methods=['POST'])
def stop_trading_script():
    """Stop the trading script"""
    try:
        state = read_trading_state()
        
        if not state.get('trading_active') or not state.get('process_id'):
            return jsonify({
                'status': 'warning',
                'message': 'No trading script is currently running'
            })
        
        # Try to terminate the process
        try:
            process = psutil.Process(state['process_id'])
            process.terminate()
            
            # Wait for process to terminate
            process.wait(timeout=10)
            
            # Update state
            state['trading_active'] = False
            state['process_id'] = None
            state['last_stopped'] = datetime.now().isoformat()
            state['script_status'] = 'stopped'
            write_trading_state(state)
            
            log_trading_event("Trading script stopped successfully")
            
            return jsonify({
                'status': 'success',
                'message': 'Trading script stopped successfully'
            })
            
        except psutil.NoSuchProcess:
            # Process doesn't exist, update state
            state['trading_active'] = False
            state['process_id'] = None
            state['script_status'] = 'stopped'
            write_trading_state(state)
            
            return jsonify({
                'status': 'success',
                'message': 'Process was not running, state updated'
            })
            
        except psutil.TimeoutExpired:
            # Force kill if timeout
            process.kill()
            state['trading_active'] = False
            state['process_id'] = None
            state['script_status'] = 'stopped'
            write_trading_state(state)
            
            return jsonify({
                'status': 'success',
                'message': 'Trading script force stopped'
            })
            
    except Exception as e:
        log_trading_event(f"Error stopping script: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error stopping trading script: {str(e)}'
        }), 500

# STEP 5: Route to Generate and Show Reports
@app.route('/SiddarthaDas_trading/generate_report', methods=['POST'])
def generate_trading_report():
    """Generate trading report from CSV"""
    try:
        data = request.get_json()
        csv_file = data.get('csv_file')
        
        if not csv_file:
            return jsonify({
                'status': 'error',
                'message': 'CSV file name is required'
            }), 400
        
        if not os.path.exists(csv_file):
            return jsonify({
                'status': 'error',
                'message': f'CSV file {csv_file} not found'
            }), 404
        
        # Import and use your HTML report generator
        import sys
        sys.path.append('.')  # Add current directory to path
        
        from Html_Play import NiftyOptionsAnalyzer
        
        # Create analyzer and generate report
        analyzer = NiftyOptionsAnalyzer(lot_size=75)
        output_file = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        # Process the file
        result = analyzer.process_file(csv_file, output_file)
        
        if result:
            log_trading_event(f"Report generated: {output_file}")
            return jsonify({
                'status': 'success',
                'message': f'Report generated successfully: {output_file}',
                'report_file': output_file
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to generate report'
            }), 500
            
    except Exception as e:
        log_trading_event(f"Error generating report: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error generating report: {str(e)}'
        }), 500

@app.route('/SiddarthaDas_trading/view_report/<filename>')
def view_trading_report(filename):
    """View generated HTML report"""
    try:
        if not filename.endswith('.html'):
            filename += '.html'
        
        if not os.path.exists(filename):
            flash(f'Report file {filename} not found', 'error')
            return redirect(url_for('trading_dashboard'))
        
        # Read and serve the HTML file
        with open(filename, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        return html_content
        
    except Exception as e:
        flash(f'Error viewing report: {str(e)}', 'error')
        return redirect(url_for('trading_dashboard'))

# API Routes for AJAX calls
@app.route('/SiddarthaDas_trading/api/status')
def get_trading_status():
    """Get current trading status via API"""
    state = read_trading_state()
    
    # Check if process is actually running
    if state.get('process_id'):
        try:
            process = psutil.Process(state['process_id'])
            state['process_running'] = process.is_running()
        except:
            state['process_running'] = False
    else:
        state['process_running'] = False
    
    return jsonify(state)

@app.route('/SiddarthaDas_trading/api/logs')
def get_recent_logs():
    """Get recent trading logs via API"""
    try:
        logs = []
        if os.path.exists(TRADING_LOG_FILE):
            with open(TRADING_LOG_FILE, 'r') as f:
                lines = f.readlines()
                logs = lines[-10:]  # Last 10 lines
                logs.reverse()  # Most recent first
        
        return jsonify({
            'status': 'success',
            'logs': logs
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

# Helper route to check token validity
@app.route('/SiddarthaDas_trading/check_token')
def check_token_validity():
    """Check if current access token is valid"""
    try:
        state = read_trading_state()
        
        if not state.get('access_token'):
            return jsonify({
                'status': 'error',
                'message': 'No access token found'
            })
        
        # Try to initialize Fyers with current token
        from fyers_apiv3 import fyersModel
        
        fyers = fyersModel.FyersModel(
            client_id=CLIENT_ID,
            is_async=False,
            token=state['access_token'],
            log_path=None
        )
        
        # Try to get profile to check if token is valid
        profile = fyers.get_profile()
        
        if profile.get('s') == 'ok':
            return jsonify({
                'status': 'success',
                'message': 'Access token is valid',
                'token_date': state.get('token_date')
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Access token is invalid or expired'
            })
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error checking token: {str(e)}'
        })

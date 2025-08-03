import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import pandas as pd
import threading
import time
from datetime import datetime
import sys
import os

# Add the parent directory to the path to import the BinanceKlineWebSocket class
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from classes.binance_kline_websocket import BinanceKlineWebSocket

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Real-Time Crypto Price Dashboard"

# Global variables to store data
price_data = {}  # Stores current price, volume, and last update time for each asset
price_history = {}  # Stores historical price data for charting
websocket = None  # WebSocket connection instance

# Default assets to monitor
DEFAULT_ASSETS = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'DOTUSDT', 'LINKUSDT']
MAX_HISTORY_POINTS = 100  # Maximum number of historical data points to keep

# Initialize data structures
for asset in DEFAULT_ASSETS:
    price_data[asset] = {
        'current_price': 0.0,
        'volume': 0.0,
        'last_update': None
    }
    price_history[asset] = []

def initialize_websocket():
    """
    Initialize the WebSocket connection to Binance for real-time price data.
    
    This function:
    1. Creates a new BinanceKlineWebSocket instance if none exists
    2. Sets up a callback function to handle incoming price updates
    3. Starts the WebSocket connection
    4. Updates global price_data and price_history when new data arrives
    """
    global websocket
    
    if websocket is None:
        websocket = BinanceKlineWebSocket(DEFAULT_ASSETS, interval="1m")
        
        def on_price_update(df):
            """
            Callback function for price updates from WebSocket.
            
            Args:
                df: DataFrame containing price data with columns: symbol, price, volume, timestamp
            
            This function:
            1. Extracts price, volume, and timestamp from the incoming data
            2. Updates the current price data for the symbol
            3. Adds the data point to historical data
            4. Maintains only the last MAX_HISTORY_POINTS to prevent memory bloat
            """
            if not df.empty:
                symbol = df['symbol'].iloc[0]
                price = df['price'].iloc[0]
                volume = df['volume'].iloc[0]
                timestamp = df['timestamp'].iloc[0]
                
                # Update price data
                if symbol in price_data:
                    price_data[symbol]['current_price'] = price
                    price_data[symbol]['volume'] = volume
                    price_data[symbol]['last_update'] = timestamp
                    
                    # Add to history
                    price_history[symbol].append({
                        'timestamp': timestamp,
                        'price': price,
                        'volume': volume
                    })
                    
                    # Keep only last MAX_HISTORY_POINTS
                    if len(price_history[symbol]) > MAX_HISTORY_POINTS:
                        price_history[symbol] = price_history[symbol][-MAX_HISTORY_POINTS:]
        
        websocket.add_callback(on_price_update)
        websocket.start()
        print("WebSocket started!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

def create_price_card(symbol):
    """
    Create a Bootstrap card component to display price information for a specific symbol.
    
    Args:
        symbol (str): The trading symbol (e.g., 'BTCUSDT')
    
    Returns:
        dbc.Card: A Bootstrap card component with:
        - Symbol name as title
        - Current price display (updated via callback)
        - Volume information (updated via callback)
        - Last update timestamp (updated via callback)
    """
    return dbc.Card([
        dbc.CardBody([
            html.H4(symbol, className="card-title"),
            html.H2(id=f"price-{symbol}", className="text-primary mb-2"),
            html.Small(id=f"volume-{symbol}", className="text-muted"),
            html.Br(),
            html.Small(id=f"last-update-{symbol}", className="text-muted")
        ])
    ], className="mb-3")

def create_layout():
    """
    Create the main dashboard layout using Bootstrap components.
    
    Returns:
        dbc.Container: The complete dashboard layout containing:
        1. Header with title
        2. Control panel with start/stop buttons and status indicator
        3. Price cards for each monitored asset
        4. Volume chart showing current volumes
        5. Interval component for automatic updates
    """
    return dbc.Container([
        # Header
        dbc.Row([
            dbc.Col([
                html.H1("Real-Time Crypto Price Dashboard", 
                       className="text-center mb-4 text-primary"),
                html.Hr()
            ])
        ]),
        
        # Control Panel
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Control Panel", className="card-title"),
                        dbc.Row([
                            dbc.Col([
                                dbc.Button("Start WebSocket", id="start-btn", 
                                          color="success", className="me-2"),
                                dbc.Button("Stop WebSocket", id="stop-btn", 
                                          color="danger", className="me-2"),
                            ]),
                            dbc.Col([
                                html.Div(id="status-indicator", className="d-inline-block")
                            ])
                        ])
                    ])
                ], className="mb-4")
            ])
        ]),
        
        # Price Cards
        dbc.Row([
            dbc.Col([create_price_card(symbol)]) 
            for symbol in DEFAULT_ASSETS
        ], className="mb-4"),
        
        # Volume Chart
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Volume Chart", className="card-title"),
                        dcc.Graph(id="volume-chart", style={'height': '400px'})
                    ])
                ])
            ])
        ], className="mb-4"),
        
        # Interval component for updates
        dcc.Interval(
            id='interval-component',
            interval=1*1000,  # in milliseconds (1 second)
            n_intervals=0
        )
    ], fluid=True)

app.layout = create_layout()

# Callbacks
@app.callback(
    [Output(f"price-{symbol}", "children") for symbol in DEFAULT_ASSETS] +
    [Output(f"volume-{symbol}", "children") for symbol in DEFAULT_ASSETS] +
    [Output(f"last-update-{symbol}", "children") for symbol in DEFAULT_ASSETS] +
    [Output("status-indicator", "children")] +
    [Output("volume-chart", "figure")],
    [Input("interval-component", "n_intervals")]
)
def update_dashboard(n):
    """
    Main dashboard update callback that runs every second.
    
    Args:
        n: Number of intervals (provided by dcc.Interval component)
    
    Returns:
        tuple: Multiple outputs including:
        - Price strings for each asset
        - Volume strings for each asset  
        - Last update strings for each asset
        - WebSocket connection status indicator
        - Volume chart figure
    
    This function:
    1. Formats current price data for display
    2. Formats volume data for display
    3. Formats last update timestamps
    4. Determines WebSocket connection status
    5. Creates a bar chart showing current volumes for all assets
    """
    
    # Update price cards
    price_outputs = []
    volume_outputs = []
    update_outputs = []
    
    for symbol in DEFAULT_ASSETS:
        data = price_data[symbol]
        price = data['current_price']
        volume = data['volume']
        last_update = data['last_update']
        
        # Format price with dollar sign and commas
        if price > 0:
            price_str = f"${price:,.2f}"
        else:
            price_str = "N/A"
        
        # Format volume with commas
        if volume > 0:
            volume_str = f"Vol: {volume:,.0f}"
        else:
            volume_str = "Vol: N/A"
        
        # Format last update timestamp
        if last_update:
            update_str = f"Updated: {last_update.strftime('%H:%M:%S')}"
        else:
            update_str = "No data"
        
        price_outputs.append(price_str)
        volume_outputs.append(volume_str)
        update_outputs.append(update_str)
    
    # Status indicator - shows connection status with colored dot
    if websocket and websocket.is_running():
        status = html.Span("🟢 Connected", className="text-success")
    else:
        status = html.Span("🔴 Disconnected", className="text-danger")
    
    # Create volume chart using Plotly
    volume_fig = go.Figure()
    for symbol in DEFAULT_ASSETS:
        if price_history[symbol]:
            df = pd.DataFrame(list(price_history[symbol]))
            if not df.empty:
                volume_fig.add_trace(go.Bar(
                    x=[symbol],
                    y=[df['volume'].iloc[-1] if not df.empty else 0],
                    name=symbol
                ))
    
    volume_fig.update_layout(
        title="Current Volume",
        xaxis_title="Symbol",
        yaxis_title="Volume",
        height=400,
        showlegend=False
    )
    
    return (price_outputs + volume_outputs + update_outputs + [status, volume_fig])

@app.callback(
    [Output("start-btn", "disabled"),
     Output("stop-btn", "disabled")],
    [Input("start-btn", "n_clicks"),
     Input("stop-btn", "n_clicks")]
)
def control_websocket(start_clicks, stop_clicks):
    """
    Control WebSocket start/stop functionality and button states.
    
    Args:
        start_clicks: Number of clicks on the start button
        stop_clicks: Number of clicks on the stop button
    
    Returns:
        tuple: (start_button_disabled, stop_button_disabled)
    
    This function:
    1. Determines which button was clicked using callback context
    2. Starts or stops the WebSocket connection accordingly
    3. Manages button states (disabled/enabled) to prevent conflicting actions
    4. Ensures only one action can be performed at a time
    """
    global websocket
    
    from dash import callback_context
    ctx = callback_context
    if not ctx.triggered:
        return False, True  # Initial state: start enabled, stop disabled
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == "start-btn" and start_clicks:
        initialize_websocket()
        return True, False  # Start disabled, stop enabled
    elif button_id == "stop-btn" and stop_clicks:
        if websocket:
            websocket.stop()
        return False, True  # Start enabled, stop disabled
    
    return False, True


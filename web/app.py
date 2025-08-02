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
price_data = {}
price_history = {}
websocket = None

# Default assets to monitor
DEFAULT_ASSETS = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'DOTUSDT', 'LINKUSDT']
MAX_HISTORY_POINTS = 100

# Initialize data structures
for asset in DEFAULT_ASSETS:
    price_data[asset] = {
        'current_price': 0.0,
        'volume': 0.0,
        'last_update': None
    }
    price_history[asset] = []

def initialize_websocket():
    """Initialize the WebSocket connection"""
    global websocket
    
    if websocket is None:
        websocket = BinanceKlineWebSocket(DEFAULT_ASSETS, interval="1m")
        
        def on_price_update(df):
            """Callback function for price updates"""
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

def create_price_card(symbol):
    """Create a price card component"""
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
    """Create the main layout"""
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
    """Update all dashboard components"""
    
    # Update price cards
    price_outputs = []
    volume_outputs = []
    update_outputs = []
    
    for symbol in DEFAULT_ASSETS:
        data = price_data[symbol]
        price = data['current_price']
        volume = data['volume']
        last_update = data['last_update']
        
        # Format price
        if price > 0:
            price_str = f"${price:,.2f}"
        else:
            price_str = "N/A"
        
        # Format volume
        if volume > 0:
            volume_str = f"Vol: {volume:,.0f}"
        else:
            volume_str = "Vol: N/A"
        
        # Format last update
        if last_update:
            update_str = f"Updated: {last_update.strftime('%H:%M:%S')}"
        else:
            update_str = "No data"
        
        price_outputs.append(price_str)
        volume_outputs.append(volume_str)
        update_outputs.append(update_str)
    
    # Status indicator
    if websocket and websocket.is_running():
        status = html.Span("🟢 Connected", className="text-success")
    else:
        status = html.Span("🔴 Disconnected", className="text-danger")
    
    # Create volume chart
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
    """Control WebSocket start/stop"""
    global websocket
    
    from dash import callback_context
    ctx = callback_context
    if not ctx.triggered:
        return False, True
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == "start-btn" and start_clicks:
        initialize_websocket()
        return True, False
    elif button_id == "stop-btn" and stop_clicks:
        if websocket:
            websocket.stop()
        return False, True
    
    return False, True


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
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from classes.binance_kline_websocket import BinanceKlineWebSocket

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
    """
    global websocket
    
    if websocket is None:
        websocket = BinanceKlineWebSocket(DEFAULT_ASSETS, interval="1m")
        
        def on_price_update(df):
            """
            Callback function for price updates from WebSocket.
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

def create_price_card(symbol):
    """
    Create a Bootstrap card component to display price information for a specific symbol.
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

def create_dashboard_layout():
    """
    Create the dashboard layout for prices and volume.
    """
    return dbc.Container([
        # Header
        dbc.Row([
            dbc.Col([
                html.H2("Dashboard de Precios y Volumen", 
                       className="text-center mb-4 text-primary"),
                html.Hr()
            ])
        ]),
        
        # Control Panel
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Panel de Control", className="card-title"),
                        dbc.Row([
                            dbc.Col([
                                dbc.Button("Iniciar WebSocket", id="start-btn", 
                                          color="success", className="me-2"),
                                dbc.Button("Detener WebSocket", id="stop-btn", 
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
                        html.H5("Gráfico de Volumen", className="card-title"),
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

def get_dashboard_callbacks(app):
    """
    Register all dashboard callbacks with the app.
    """
    
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
                update_str = f"Actualizado: {last_update.strftime('%H:%M:%S')}"
            else:
                update_str = "Sin datos"
            
            price_outputs.append(price_str)
            volume_outputs.append(volume_str)
            update_outputs.append(update_str)
        
        # Status indicator - shows connection status with colored dot
        if websocket and websocket.is_running():
            status = html.Span("🟢 Conectado", className="text-success")
        else:
            status = html.Span("🔴 Desconectado", className="text-danger")
        
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
            title="Volumen Actual",
            xaxis_title="Símbolo",
            yaxis_title="Volumen",
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
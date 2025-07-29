#!/usr/bin/env python3
"""
Dashboard web para el bot de arbitraje triangular

Esta aplicación Dash proporciona:
1. Monitoreo de precios en tiempo real
2. Visualización de oportunidades de arbitraje
3. Gráficos interactivos
4. Panel de control del bot
"""

import dash
from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import requests
import json
import time
from datetime import datetime, timedelta
import threading
import queue

# Configuración de la aplicación Dash
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    suppress_callback_exceptions=True
)

# Configuración del servidor
app.config.suppress_callback_exceptions = True

# Cola para datos en tiempo real
data_queue = queue.Queue()

# Estado global de la aplicación
app_state = {
    'prices': {},
    'opportunities': [],
    'websocket_connected': False,
    'last_update': None
}

def fetch_api_data():
    """Obtiene datos de la API"""
    try:
        # Obtener precios actuales
        prices_response = requests.get('http://localhost:8000/api/prices', timeout=5)
        if prices_response.status_code == 200:
            app_state['prices'] = prices_response.json()['prices']
        
        # Obtener oportunidades
        opportunities_response = requests.get('http://localhost:8000/api/opportunities', timeout=5)
        if opportunities_response.status_code == 200:
            app_state['opportunities'] = opportunities_response.json()['opportunities']
        
        # Obtener estado del sistema
        status_response = requests.get('http://localhost:8000/api/status', timeout=5)
        if status_response.status_code == 200:
            status_data = status_response.json()
            app_state['websocket_connected'] = status_data['websocket_running']
            app_state['last_update'] = status_data['timestamp']
            
    except Exception as e:
        print(f"Error obteniendo datos de la API: {e}")

def create_price_chart():
    """Crea el gráfico de precios"""
    if not app_state['prices']:
        return go.Figure().add_annotation(
            text="No hay datos disponibles",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
    
    # Preparar datos para el gráfico
    symbols = list(app_state['prices'].keys())
    prices = [app_state['prices'][symbol]['price'] for symbol in symbols]
    colors = ['#00ff00', '#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4']
    
    fig = go.Figure(data=[
        go.Bar(
            x=symbols,
            y=prices,
            marker_color=colors[:len(symbols)],
            text=[f"${price:,.2f}" for price in prices],
            textposition='auto',
        )
    ])
    
    fig.update_layout(
        title="Precios Actuales",
        xaxis_title="Símbolos",
        yaxis_title="Precio (USDT)",
        template="plotly_dark",
        height=400,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    return fig

def create_opportunities_table():
    """Crea la tabla de oportunidades de arbitraje"""
    if not app_state['opportunities']:
        return html.Div(
            "No hay oportunidades de arbitraje disponibles",
            className="text-center text-muted mt-3"
        )
    
    # Tomar las últimas 10 oportunidades
    recent_opportunities = app_state['opportunities'][-10:]
    
    rows = []
    for opp in reversed(recent_opportunities):
        profit_color = "success" if opp['profit_percentage'] > 1.0 else "warning"
        
        row = dbc.Tr([
            dbc.Td(opp['route']),
            dbc.Td(f"{opp['profit_percentage']:.2f}%", className=f"text-{profit_color}"),
            dbc.Td(opp['timestamp'][:19]),  # Solo fecha y hora
        ])
        rows.append(row)
    
    table = dbc.Table([
        dbc.Thead([
            dbc.Tr([
                dbc.Th("Ruta"),
                dbc.Th("Profit %"),
                dbc.Th("Timestamp")
            ])
        ]),
        dbc.Tbody(rows)
    ], striped=True, bordered=True, hover=True, dark=True)
    
    return table

def create_price_history_chart(symbol='BTCUSDT'):
    """Crea el gráfico de historial de precios"""
    try:
        response = requests.get(f'http://localhost:8000/api/prices/{symbol}', timeout=5)
        if response.status_code != 200:
            return go.Figure().add_annotation(
                text="No hay datos disponibles",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
        
        data = response.json()
        history = data['history']
        
        if not history:
            return go.Figure().add_annotation(
                text="No hay datos históricos",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
        
        df = pd.DataFrame(history)
        df['datetime'] = pd.to_datetime(df['datetime'])
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['datetime'],
            y=df['price'],
            mode='lines+markers',
            name=symbol,
            line=dict(color='#00ff00', width=2),
            marker=dict(size=4)
        ))
        
        fig.update_layout(
            title=f"Historial de Precios - {symbol}",
            xaxis_title="Tiempo",
            yaxis_title="Precio (USDT)",
            template="plotly_dark",
            height=400,
            margin=dict(l=50, r=50, t=50, b=50)
        )
        
        return fig
        
    except Exception as e:
        print(f"Error creando gráfico de historial: {e}")
        return go.Figure().add_annotation(
            text="Error cargando datos",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )

# Layout principal de la aplicación
app.layout = dbc.Container([
    # Header
    dbc.Row([
        dbc.Col([
            html.H1("🤖 Bot de Arbitraje Triangular", className="text-center mb-4"),
            html.Hr()
        ])
    ]),
    
    # Status Bar
    dbc.Row([
        dbc.Col([
            dbc.Alert([
                html.I(className="fas fa-circle me-2"),
                html.Span(id="status-text", children="Conectando...")
            ], id="status-alert", color="warning", className="mb-3")
        ])
    ]),
    
    # Main Content
    dbc.Row([
        # Panel izquierdo - Precios y Gráficos
        dbc.Col([
            # Precios actuales
            dbc.Card([
                dbc.CardHeader("📊 Precios en Tiempo Real"),
                dbc.CardBody([
                    dcc.Graph(id="price-chart", config={'displayModeBar': False}),
                    dcc.Interval(
                        id='price-interval',
                        interval=2000,  # Actualizar cada 2 segundos
                        n_intervals=0
                    )
                ])
            ], className="mb-4"),
            
            # Historial de precios
            dbc.Card([
                dbc.CardHeader([
                    "📈 Historial de Precios",
                    dbc.Select(
                        id="symbol-selector",
                        options=[
                            {"label": "BTCUSDT", "value": "BTCUSDT"},
                            {"label": "ETHUSDT", "value": "ETHUSDT"},
                            {"label": "BNBUSDT", "value": "BNBUSDT"},
                            {"label": "ADAUSDT", "value": "ADAUSDT"},
                            {"label": "DOTUSDT", "value": "DOTUSDT"}
                        ],
                        value="BTCUSDT",
                        className="float-end"
                    )
                ]),
                dbc.CardBody([
                    dcc.Graph(id="history-chart", config={'displayModeBar': False}),
                    dcc.Interval(
                        id='history-interval',
                        interval=5000,  # Actualizar cada 5 segundos
                        n_intervals=0
                    )
                ])
            ])
        ], md=8),
        
        # Panel derecho - Oportunidades y Control
        dbc.Col([
            # Oportunidades de arbitraje
            dbc.Card([
                dbc.CardHeader("💰 Oportunidades de Arbitraje"),
                dbc.CardBody([
                    html.Div(id="opportunities-table"),
                    dcc.Interval(
                        id='opportunities-interval',
                        interval=3000,  # Actualizar cada 3 segundos
                        n_intervals=0
                    )
                ])
            ], className="mb-4"),
            
            # Panel de control
            dbc.Card([
                dbc.CardHeader("🎮 Panel de Control"),
                dbc.CardBody([
                    dbc.Button(
                        "🔄 Actualizar Datos",
                        id="refresh-btn",
                        color="primary",
                        className="w-100 mb-2"
                    ),
                    dbc.Button(
                        "📊 Ver Estadísticas",
                        id="stats-btn",
                        color="info",
                        className="w-100 mb-2"
                    ),
                    html.Hr(),
                    html.H6("Información del Sistema:"),
                    html.P(id="system-info", className="small")
                ])
            ])
        ], md=4)
    ]),
    
    # Footer
    dbc.Row([
        dbc.Col([
            html.Hr(),
            html.P(
                "Bot de Arbitraje Triangular - Monitoreo en Tiempo Real",
                className="text-center text-muted"
            )
        ])
    ])
], fluid=True, className="mt-3")

# Callbacks
@app.callback(
    [Output("price-chart", "figure"),
     Output("status-alert", "color"),
     Output("status-text", "children")],
    [Input("price-interval", "n_intervals"),
     Input("refresh-btn", "n_clicks")]
)
def update_price_chart(n_intervals, n_clicks):
    """Actualiza el gráfico de precios y el estado"""
    fetch_api_data()
    
    # Determinar color del estado
    if app_state['websocket_connected']:
        status_color = "success"
        status_text = "✅ Conectado - WebSocket activo"
    else:
        status_color = "danger"
        status_text = "❌ Desconectado - WebSocket inactivo"
    
    return create_price_chart(), status_color, status_text

@app.callback(
    Output("history-chart", "figure"),
    [Input("history-interval", "n_intervals"),
     Input("symbol-selector", "value")]
)
def update_history_chart(n_intervals, symbol):
    """Actualiza el gráfico de historial"""
    return create_price_history_chart(symbol)

@app.callback(
    Output("opportunities-table", "children"),
    [Input("opportunities-interval", "n_intervals")]
)
def update_opportunities_table(n_intervals):
    """Actualiza la tabla de oportunidades"""
    return create_opportunities_table()

@app.callback(
    Output("system-info", "children"),
    [Input("price-interval", "n_intervals")]
)
def update_system_info(n_intervals):
    """Actualiza la información del sistema"""
    if app_state['last_update']:
        last_update = datetime.fromisoformat(app_state['last_update'].replace('Z', '+00:00'))
        time_diff = datetime.now(last_update.tzinfo) - last_update
        
        info = f"""
        📡 WebSocket: {'✅ Activo' if app_state['websocket_connected'] else '❌ Inactivo'}
        📊 Símbolos: {len(app_state['prices'])}
        💰 Oportunidades: {len(app_state['opportunities'])}
        ⏰ Última actualización: {time_diff.total_seconds():.0f}s atrás
        """
        return info
    return "Cargando información del sistema..."

# Función para ejecutar la aplicación
def run_dashboard():
    """Ejecuta el dashboard"""
    print(">>> Iniciando Dashboard de Arbitraje Triangular...")
    print(">>> Accede a: http://localhost:8050")
    print(">>> API disponible en: http://localhost:8000")
    
    app.run_server(
        debug=True,
        host='0.0.0.0',
        port=8050,
        dev_tools_hot_reload=False
    )

if __name__ == "__main__":
    run_dashboard() 
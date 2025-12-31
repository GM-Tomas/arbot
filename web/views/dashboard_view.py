import dash
from dash import dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import sys
import os

# Add the parent directory to the path to import the classes
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from classes.price_monitor import PriceMonitor

def create_price_card(symbol, price_data):
    """
    Crea una tarjeta Bootstrap con la información del precio.
    Vista pura: recibe datos -> devuelve componente.
    """
    price = price_data.get('price', 0)
    volume = price_data.get('volume', 0)
    timestamp = price_data.get('last_update_str', 'N/A')
    
    # Formateo
    price_str = f"${price:,.2f}" if price > 0 else "Cargando..."
    volume_str = f"Vol: {volume:,.0f}" if volume > 0 else ""
    
    return dbc.Col([
        dbc.Card([
            dbc.CardBody([
                html.H4(symbol, className="card-title text-center"),
                html.H2(price_str, className="text-primary text-center mb-2"),
                html.Small(volume_str, className="text-muted d-block text-center"),
                html.Small(f"Act: {timestamp}", className="text-muted d-block text-center mt-2")
            ])
        ], className="mb-3 shadow-sm")
    ], width=12, sm=6, md=4, lg=3)

def create_dashboard_layout():
    """
    Crea el layout del dashboard.
    """
    monitor = PriceMonitor.get_instance()
    current_pairs = ", ".join(monitor.get_monitored_pairs())

    return dbc.Container([
        # Header
        dbc.Row([
            dbc.Col([
                html.H2("Monitor de Precios Crypto", 
                       className="text-center mb-4 text-primary"),
                html.Hr()
            ])
        ]),
        
        # Panel de Configuración (Input Dinámico)
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Configuración de Pares"),
                    dbc.CardBody([
                        dbc.Label("Ingresa los pares a monitorear (separados por coma):"),
                        dbc.Textarea(
                            id="pairs-input",
                            placeholder="Ej: BTCUSDT, ETHUSDT, SOLUSDT",
                            value=current_pairs,
                            style={"height": "100px"},
                            className="mb-3"
                        ),
                        dbc.Button("Actualizar Pares", id="update-pairs-btn", color="primary", outline=True)
                    ])
                ], className="mb-4")
            ], width=12, md=8, lg=6, className="mx-auto")
        ]),
        
        # Contenedor de Tarjetas de Precios
        html.Div(id="cards-container", className="row"),
        
        # Intervalo de actualización (1 segundo)
        dcc.Interval(
            id='interval-component',
            interval=1000,
            n_intervals=0
        )
    ], fluid=True)

def get_dashboard_callbacks(app):
    """
    Registra los callbacks (Controlador).
    """
    
    @app.callback(
        [Output("cards-container", "children"),
         Output("pairs-input", "value")],
        [Input("interval-component", "n_intervals"),
         Input("update-pairs-btn", "n_clicks")],
        [State("pairs-input", "value")]
    )
    def update_dashboard(n_intervals, n_clicks, pairs_input_value):
        """
        Callback único que maneja tanto la actualización de tiempo como el botón.
        """
        monitor = PriceMonitor.get_instance()
        ctx = callback_context
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None
        
        # LÓGICA DEL CONTROLADOR
        
        # 1. Si se clickeó el botón, actualizar el modelo
        if triggered_id == "update-pairs-btn":
            if pairs_input_value:
                pairs_list = pairs_input_value.split(',')
                monitor.update_pairs(pairs_list)
        
        # 2. Obtener datos del modelo (siempre, para refrescar la vista)
        prices = monitor.get_prices()
        monitored_pairs = monitor.get_monitored_pairs()
        
        # 3. Generar la VISTA (Tarjetas)
        cards = []
        for pair in monitored_pairs:
            # Si tenemos datos, usarlos, si no, placeholder
            data = prices.get(pair, {})
            cards.append(create_price_card(pair, data))
            
        if not cards:
            cards = [dbc.Alert("No hay pares configurados o datos recibidos.", color="warning")]
            
        # Devolver visualización y el valor actual del input (para mantener sincronía)
        return cards, ", ".join(monitored_pairs)
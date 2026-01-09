import dash
from dash import dcc, html, Input, Output
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
    return dbc.Container([
        # Header
        dbc.Row([
            dbc.Col([
                html.H2("Crypto Monitor", 
                       className="text-center mb-4 text-primary"),
                html.Hr()
            ])
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
        Output("cards-container", "children"),
        [Input("interval-component", "n_intervals")]
    )
    def update_dashboard(n_intervals):
        """
        Callback único que actualiza la vista basado en el modelo.
        """
        monitor = PriceMonitor.get_instance()
        
        # Obtener datos del modelo
        prices = monitor.get_prices()
        monitored_pairs = monitor.get_monitored_pairs()
        
        # Generar la VISTA (Tarjetas)
        cards = []
        for pair in monitored_pairs:
            # Si tenemos datos, usarlos, si no, placeholder
            data = prices.get(pair, {})
            cards.append(create_price_card(pair, data))
            
        if not cards:
            cards = [dbc.Alert("No hay pares configurados en config/pairs.json", color="warning")]
            
        return cards
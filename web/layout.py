import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from views.dashboard_view import create_dashboard_layout

def create_main_layout():
    """
    Create the main layout. Minimalist: just the dashboard content.
    """
    return html.Div([
        # Directamente renderizamos el dashboard, sin navegación compleja
        create_dashboard_layout()
    ])
import dash
import dash_bootstrap_components as dbc
import sys
import os

# Add the parent directory to the path to import the views
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from layout import create_main_layout
from views.dashboard_view import get_dashboard_callbacks
from classes.price_monitor import PriceMonitor

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Crypto Price Monitor"

# Initialize PriceMonitor Singleton early
PriceMonitor.get_instance()

# Set up the main layout
app.layout = create_main_layout()

# Register dashboard callbacks
get_dashboard_callbacks(app)

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8050)

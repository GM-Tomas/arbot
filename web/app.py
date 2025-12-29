import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import sys
import os

# Add the parent directory to the path to import the views
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from layout import create_main_layout
from views.dashboard_view import create_dashboard_layout, get_dashboard_callbacks
from views.arbitrage_view import create_arbitrage_layout, get_arbitrage_callbacks

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Arbitbot Dashboard"

# Set up the main layout with navigation
app.layout = create_main_layout()

# Register dashboard callbacks
get_dashboard_callbacks(app)

# Register arbitrage callbacks
get_arbitrage_callbacks(app)

# Callback to handle page routing
@app.callback(
    Output("page-content", "children"),
    [Input("url", "pathname")]
)
def display_page(pathname):
    """
    Handle page routing based on URL pathname.
    """
    if pathname == "/" or pathname == "/dashboard":
        return create_dashboard_layout()
    elif pathname == "/arbitrage":
        return create_arbitrage_layout()
    else:
        return create_dashboard_layout()  # Default to dashboard

# Add URL routing
app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    create_main_layout()
])

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8050)


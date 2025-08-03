import dash
from dash import dcc, html
import dash_bootstrap_components as dbc

def create_main_layout():
    """
    Create the main layout with navigation between dashboard and arbitrage pages.
    
    Returns:
        dbc.Container: The main layout with navigation and content area
    """
    return dbc.Container([
        # Navigation Header
        dbc.Row([
            dbc.Col([
                html.H1("Arbitbot Dashboard", 
                       className="text-center mb-4 text-primary"),
                dbc.Nav([
                    dbc.NavItem(dbc.NavLink("Dashboard de Precios", href="/", id="nav-dashboard")),
                    dbc.NavItem(dbc.NavLink("Oportunidades de Arbitraje", href="/arbitrage", id="nav-arbitrage")),
                ], className="justify-content-center mb-4"),
                html.Hr()
            ])
        ]),
        
        # Content Area
        html.Div(id="page-content")
        
    ], fluid=True) 
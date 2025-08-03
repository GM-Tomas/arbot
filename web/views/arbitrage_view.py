import dash
from dash import dcc, html
import dash_bootstrap_components as dbc

def create_arbitrage_layout():
    """
    Create the arbitrage opportunities layout with title and description.
    """
    return dbc.Container([
        # Header
        dbc.Row([
            dbc.Col([
                html.H2("Oportunidades de Arbitraje", 
                       className="text-center mb-4 text-primary"),
                html.Hr()
            ])
        ]),
        
        # Content
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H3("Análisis de Arbitraje", className="card-title text-center mb-4"),
                        html.P([
                            "Esta página está diseñada para mostrar oportunidades de arbitraje entre diferentes exchanges y pares de trading. ",
                            "El sistema analiza las diferencias de precios en tiempo real para identificar posibles ganancias."
                        ], className="lead text-center mb-4"),
                        html.P([
                            "Características principales:",
                            html.Ul([
                                html.Li("Detección automática de diferencias de precios"),
                                html.Li("Cálculo de márgenes de ganancia"),
                                html.Li("Alertas en tiempo real"),
                                html.Li("Historial de oportunidades")
                            ])
                        ], className="mb-4"),
                        html.Div([
                            dbc.Alert([
                                html.H4("🚧 En Desarrollo", className="alert-heading"),
                                html.P("Esta funcionalidad está siendo implementada. Próximamente estará disponible el análisis completo de oportunidades de arbitraje.")
                            ], color="info", className="text-center")
                        ])
                    ])
                ], className="mb-4")
            ], width=8, className="mx-auto")
        ]),
        
        # Placeholder for future arbitrage content
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Próximas Funcionalidades", className="card-title"),
                        html.Ul([
                            html.Li("Comparación de precios entre exchanges"),
                            html.Li("Cálculo de spreads y márgenes"),
                            html.Li("Alertas configurables"),
                            html.Li("Backtesting de estrategias"),
                            html.Li("Reportes de rentabilidad")
                        ])
                    ])
                ])
            ])
        ])
    ], fluid=True) 
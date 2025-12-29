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

# Add the parent directory to the path to import the ArbitrageBot class
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from classes.arbitrage_bot import ArbitrageBot

# Global variables
arbitrage_bot = None
bot_thread = None
bot_running = False

def initialize_arbitrage_bot():
    """
    Initialize the arbitrage bot in a separate thread.
    """
    global arbitrage_bot, bot_thread, bot_running
    
    if arbitrage_bot is None:
        arbitrage_bot = ArbitrageBot()
        
        def run_bot():
            """Run the bot in a separate thread"""
            global bot_running
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(arbitrage_bot.start_scanning())
                
                # Keep the bot running for scanning
                while bot_running:
                    time.sleep(1)
                    
            except Exception as e:
                print(f"Error running bot: {e}")
            finally:
                bot_running = False
        
        bot_thread = threading.Thread(target=run_bot, daemon=True)
        bot_running = True
        bot_thread.start()

def create_arbitrage_layout():
    """
    Create the arbitrage opportunities layout with real-time data.
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
        
        # Bot Control Section
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Control del Bot", className="card-title text-center mb-3"),
                        dbc.Row([
                            dbc.Col([
                                dbc.Button("🚀 Iniciar Bot", id="start-bot-btn", 
                                          color="success", className="me-2", n_clicks=0),
                                dbc.Button("⏹️ Detener Bot", id="stop-bot-btn", 
                                          color="danger", className="me-2", n_clicks=0, disabled=True),
                            ], className="text-center")
                        ]),
                        html.Div(id="bot-status", className="mt-3")
                    ])
                ], className="mb-4")
            ])
        ]),
        
        # Statistics Section
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Estadísticas", className="card-title text-center mb-3"),
                        dbc.Row([
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardBody([
                                        html.H5(id="total-opportunities", children="0", className="text-center text-primary"),
                                        html.P("Oportunidades Totales", className="text-center mb-0")
                                    ])
                                ], color="light", outline=True)
                            ], width=3),
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardBody([
                                        html.H5(id="avg-profit", children="0%", className="text-center text-success"),
                                        html.P("Beneficio Promedio", className="text-center mb-0")
                                    ])
                                ], color="light", outline=True)
                            ], width=3),
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardBody([
                                        html.H5(id="max-profit", children="0%", className="text-center text-warning"),
                                        html.P("Beneficio Máximo", className="text-center mb-0")
                                    ])
                                ], color="light", outline=True)
                            ], width=3),
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardBody([
                                        html.H5(id="monitored-pairs", children="0", className="text-center text-info"),
                                        html.P("Pares Monitoreados", className="text-center mb-0")
                                    ])
                                ], color="light", outline=True)
                            ], width=3)
                        ])
                    ])
                ], className="mb-4")
            ])
        ]),
        
        # Recent Opportunities Section
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Oportunidades Recientes", className="card-title text-center mb-3"),
                        html.Div(id="opportunities-table", children=[
                            dbc.Alert("Inicia el bot para ver oportunidades de arbitraje", color="info")
                        ])
                    ])
                ], className="mb-4")
            ])
        ]),
        
        # Profit Chart Section
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Historial de Beneficios", className="card-title text-center mb-3"),
                        dcc.Graph(id="profit-chart", figure=go.Figure())
                    ])
                ])
            ])
        ]),
        
        # Hidden div for storing data
        html.Div(id="arbitrage-data", style={"display": "none"}),
        
        # Interval component for updates
        dcc.Interval(
            id="arbitrage-interval",
            interval=5000,  # Update every 5 seconds
            n_intervals=0
        )
    ], fluid=True)

def get_arbitrage_callbacks(app):
    """
    Register all arbitrage callbacks with the app.
    """
    
    @app.callback(
        [Output("start-bot-btn", "disabled"),
         Output("stop-bot-btn", "disabled"),
         Output("bot-status", "children")],
        [Input("start-bot-btn", "n_clicks"),
         Input("stop-bot-btn", "n_clicks")]
    )
    def control_bot(start_clicks, stop_clicks):
        """Control bot start/stop functionality"""
        global arbitrage_bot, bot_running
        
        from dash import callback_context
        ctx = callback_context
        if not ctx.triggered:
            return False, True, dbc.Alert("Bot detenido", color="secondary")
        
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        if button_id == "start-bot-btn" and start_clicks:
            initialize_arbitrage_bot()
            return True, False, dbc.Alert("Bot iniciado - Escaneando oportunidades...", color="success")
        elif button_id == "stop-bot-btn" and stop_clicks:
            if arbitrage_bot:
                arbitrage_bot.stop()
            return False, True, dbc.Alert("Bot detenido", color="secondary")
        
        return False, True, dbc.Alert("Bot detenido", color="secondary")
    
    @app.callback(
        [Output("total-opportunities", "children"),
         Output("avg-profit", "children"),
         Output("max-profit", "children"),
         Output("monitored-pairs", "children"),
         Output("opportunities-table", "children"),
         Output("profit-chart", "figure")],
        [Input("arbitrage-interval", "n_intervals")]
    )
    def update_arbitrage_data(n):
        """Update arbitrage data every interval"""
        global arbitrage_bot
        
        if arbitrage_bot is None:
            return "0", "0%", "0%", "0", dbc.Alert("Inicia el bot para ver oportunidades", color="info"), go.Figure()
        
        try:
            # Get dashboard data from bot
            data = arbitrage_bot.get_dashboard_data()
            
            # Extract statistics
            total_opps = data.get('opportunities', {}).get('total_found', 0)
            avg_profit = data.get('opportunities', {}).get('average_profit', 0)
            max_profit = data.get('opportunities', {}).get('max_profit', 0)
            monitored_pairs = data.get('status', {}).get('monitored_pairs', 0)
            
            # Create opportunities table
            recent_opps = data.get('opportunities', {}).get('recent', [])
            if recent_opps:
                table_rows = []
                for opp in recent_opps[-5:]:  # Show last 5 opportunities
                    profit_color = "success" if opp['profit_percentage'] > 1 else "warning"
                    table_rows.append(
                        dbc.Row([
                            dbc.Col(opp['route'], width=6),
                            dbc.Col(f"{opp['profit_percentage']:.4f}%", width=2, 
                                   className=f"text-{profit_color}"),
                            dbc.Col(f"${opp['amounts']['initial']:.2f}", width=2),
                            dbc.Col(f"${opp['amounts']['final']:.2f}", width=2)
                        ], className="mb-2")
                    )
                
                opportunities_table = [
                    dbc.Row([
                        dbc.Col("Ruta", width=6, className="fw-bold"),
                        dbc.Col("Beneficio", width=2, className="fw-bold"),
                        dbc.Col("Inicial", width=2, className="fw-bold"),
                        dbc.Col("Final", width=2, className="fw-bold")
                    ], className="mb-3 border-bottom"),
                    *table_rows
                ]
            else:
                opportunities_table = dbc.Alert("No se han encontrado oportunidades aún", color="info")
            
            # Create profit chart
            if recent_opps:
                profits = [opp['profit_percentage'] for opp in recent_opps]
                timestamps = [opp['timestamp'] for opp in recent_opps]
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=timestamps,
                    y=profits,
                    mode='lines+markers',
                    name='Beneficio (%)',
                    line=dict(color='green', width=2),
                    marker=dict(size=8)
                ))
                
                fig.update_layout(
                    title="Evolución de Beneficios",
                    xaxis_title="Tiempo",
                    yaxis_title="Beneficio (%)",
                    height=400,
                    showlegend=False
                )
            else:
                fig = go.Figure()
                fig.update_layout(
                    title="Evolución de Beneficios",
                    xaxis_title="Tiempo",
                    yaxis_title="Beneficio (%)",
                    height=400,
                    annotations=[{
                        'text': 'No hay datos disponibles',
                        'xref': 'paper',
                        'yref': 'paper',
                        'showarrow': False,
                        'font': {'size': 20}
                    }]
                )
            
            return (
                str(total_opps),
                f"{avg_profit:.2f}%",
                f"{max_profit:.2f}%",
                str(monitored_pairs),
                opportunities_table,
                fig
            )
            
        except Exception as e:
            return "0", "0%", "0%", "0", dbc.Alert(f"Error: {str(e)}", color="danger"), go.Figure() 
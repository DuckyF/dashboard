import dash
from dash import dcc, html, Input, Output, State, dash_table
import plotly.express as px
import pandas as pd
import base64
import io
from datetime import datetime as dt

app = dash.Dash(__name__)
server = app.server

app.layout = html.Div([
    # Заголовок и описание
    html.Div([
        html.H1("Анализ продаж товаров и услуг", style={'textAlign': 'center'}),
        html.P("Интерактивный дашборд для анализа динамики продаж, структуры доходов и расходов",
               style={'textAlign': 'center'}),
    ], style={'margin-bottom': '20px'}),

    html.Div([
        html.Div([
            html.Label("Выберите период анализа:"),
            dcc.Dropdown(
                id='period-selector',
                options=[
                    {'label': 'Месяц', 'value': 'M'},
                    {'label': 'Квартал', 'value': 'Q'},
                    {'label': 'Год', 'value': 'Y'}
                ],
                value='M',
                clearable=False
            )
        ], style={'width': '30%', 'display': 'inline-block', 'padding': '10px'}),

        html.Div([
            html.Label("Выберите категории:"),
            dcc.Dropdown(
                id='category-selector',
                multi=True
            )
        ], style={'width': '65%', 'display': 'inline-block', 'padding': '10px'}),
    ], style={'display': 'flex'}),

    html.Div([
        html.Div(id='revenue-indicator', style={'width': '32%', 'display': 'inline-block', 'padding': '10px'}),
        html.Div(id='expenses-indicator', style={'width': '32%', 'display': 'inline-block', 'padding': '10px'}),
        html.Div(id='profit-indicator', style={'width': '32%', 'display': 'inline-block', 'padding': '10px'}),
    ], style={'display': 'flex'}),

])


if __name__ == '__main__':
    app.run(debug=True)
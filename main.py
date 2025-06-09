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
        dcc.Upload(
            id='upload-data',
            children=html.Div([
                'Перетащите или ',
                html.A('выберите CSV файл')
            ]),
            style={
                'width': '100%',
                'height': '60px',
                'lineHeight': '60px',
                'borderWidth': '1px',
                'borderStyle': 'dashed',
                'borderRadius': '5px',
                'textAlign': 'center',
                'margin': '10px 0'
            },
            multiple=False
        ),
    ]),

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

    html.Div([
        dcc.Graph(id='timeseries-chart'),
    ], style={'width': '100%', 'padding': '10px'}),

    html.Div([
        html.Div([
            dcc.Graph(id='pie-chart'),
        ], style={'width': '48%', 'display': 'inline-block'}),

        html.Div([
            dcc.Graph(id='histogram-chart'),
        ], style={'width': '48%', 'display': 'inline-block', 'float': 'right'}),
    ]),

    html.Div([
        dash_table.DataTable(
            id='data-table',
            page_size=10,
            style_table={'overflowX': 'auto'},
            style_cell={
                'height': 'auto',
                'minWidth': '100px', 'maxWidth': '180px',
                'whiteSpace': 'normal'
            }
        )
    ], style={'padding': '10px'}),

    dcc.Store(id='stored-data')
])


def parse_contents(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        else:
            return None
    except Exception as e:
        print(e)
        return None

    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
    elif 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])

    return df


@app.callback(
    [Output('stored-data', 'data'),
     Output('category-selector', 'options')],
    [Input('upload-data', 'contents')],
    [State('upload-data', 'filename')]
)
def update_data(contents, filename):
    if contents is None:
        return dash.no_update, dash.no_update

    df = parse_contents(contents, filename)
    if df is None:
        return dash.no_update, dash.no_update

    if 'Category' in df.columns:
        categories = [{'label': cat, 'value': cat} for cat in df['Category'].unique()]
    elif 'category' in df.columns:
        categories = [{'label': cat, 'value': cat} for cat in df['category'].unique()]
    else:
        categories = []

    return df.to_dict('records'), categories


@app.callback(
    [Output('revenue-indicator', 'children'),
     Output('expenses-indicator', 'children'),
     Output('profit-indicator', 'children')],
    [Input('stored-data', 'data'),
     Input('category-selector', 'value')]
)
def update_indicators(data, selected_categories):
    if not data:
        return dash.no_update, dash.no_update, dash.no_update

    df = pd.DataFrame(data)

    if selected_categories:
        if 'Category' in df.columns:
            df = df[df['Category'].isin(selected_categories)]
        elif 'category' in df.columns:
            df = df[df['category'].isin(selected_categories)]

    revenue = df['Revenue'].sum() if 'Revenue' in df.columns else df['revenue'].sum() if 'revenue' in df.columns else 0
    expenses = df['Expenses'].sum() if 'Expenses' in df.columns else df[
        'expenses'].sum() if 'expenses' in df.columns else 0
    profit = revenue - expenses

    revenue_indicator = html.Div([
        html.H3("Выручка"),
        html.H4(f"{revenue:,.2f} ₽", style={'color': 'green'})
    ], style={'border': '1px solid #ddd', 'padding': '10px', 'border-radius': '5px', 'text-align': 'center'})

    expenses_indicator = html.Div([
        html.H3("Расходы"),
        html.H4(f"{expenses:,.2f} ₽", style={'color': 'red'})
    ], style={'border': '1px solid #ddd', 'padding': '10px', 'border-radius': '5px', 'text-align': 'center'})

    profit_indicator = html.Div([
        html.H3("Прибыль"),
        html.H4(f"{profit:,.2f} ₽", style={'color': 'blue'})
    ], style={'border': '1px solid #ddd', 'padding': '10px', 'border-radius': '5px', 'text-align': 'center'})

    return revenue_indicator, expenses_indicator, profit_indicator


@app.callback(
    Output('timeseries-chart', 'figure'),
    [Input('stored-data', 'data'),
     Input('period-selector', 'value'),
     Input('category-selector', 'value')]
)
def update_timeseries(data, period, selected_categories):
    if not data:
        return dash.no_update

    df = pd.DataFrame(data)

    date_col = 'Date' if 'Date' in df.columns else 'date' if 'date' in df.columns else None
    if not date_col:
        return px.line(title="Нет данных о дате")

    if selected_categories:
        if 'Category' in df.columns:
            df = df[df['Category'].isin(selected_categories)]
        elif 'category' in df.columns:
            df = df[df['category'].isin(selected_categories)]

    df[date_col] = pd.to_datetime(df[date_col])
    df.set_index(date_col, inplace=True)

    revenue_col = 'Revenue' if 'Revenue' in df.columns else 'revenue' if 'revenue' in df.columns else None
    expenses_col = 'Expenses' if 'Expenses' in df.columns else 'expenses' if 'expenses' in df.columns else None

    if not revenue_col or not expenses_col:
        return px.line(title="Нет данных о доходах/расходах")

    resampled = df.resample(period).sum()
    resampled.reset_index(inplace=True)

    fig = px.line(resampled, x=date_col, y=[revenue_col, expenses_col],
                  title="Динамика доходов и расходов",
                  labels={'value': 'Сумма', 'variable': 'Показатель'})

    fig.update_layout(
        hovermode='x unified',
        legend_title='Показатели'
    )

    return fig


@app.callback(
    Output('pie-chart', 'figure'),
    [Input('stored-data', 'data'),
     Input('period-selector', 'value'),
     Input('category-selector', 'value')]
)
def update_pie_chart(data, period, selected_categories):
    if not data:
        return dash.no_update

    df = pd.DataFrame(data)

    if selected_categories:
        if 'Category' in df.columns:
            df = df[df['Category'].isin(selected_categories)]
        elif 'category' in df.columns:
            df = df[df['category'].isin(selected_categories)]

    expenses_col = 'Expenses' if 'Expenses' in df.columns else 'expenses' if 'expenses' in df.columns else None
    category_col = 'Category' if 'Category' in df.columns else 'category' if 'category' in df.columns else None

    if not expenses_col or not category_col:
        return px.pie(title="Нет данных о расходах по категориям")

    grouped = df.groupby(category_col)[expenses_col].sum().reset_index()

    fig = px.pie(grouped, values=expenses_col, names=category_col,
                 title="Структура расходов по категориям",
                 hover_data=[expenses_col])

    fig.update_traces(textposition='inside', textinfo='percent+label')

    return fig


@app.callback(
    Output('histogram-chart', 'figure'),
    [Input('stored-data', 'data'),
     Input('category-selector', 'value')]
)
def update_histogram(data, selected_categories):
    if not data:
        return dash.no_update

    df = pd.DataFrame(data)

    if selected_categories:
        if 'Category' in df.columns:
            df = df[df['Category'].isin(selected_categories)]
        elif 'category' in df.columns:
            df = df[df['category'].isin(selected_categories)]

    revenue_col = 'Revenue' if 'Revenue' in df.columns else 'revenue' if 'revenue' in df.columns else None
    expenses_col = 'Expenses' if 'Expenses' in df.columns else 'expenses' if 'expenses' in df.columns else None

    if not revenue_col or not expenses_col:
        return px.bar(title="Нет данных для расчета прибыли")

    df['Profit'] = df[revenue_col] - df[expenses_col]

    fig = px.histogram(df, x='Profit', nbins=20,
                       title="Распределение прибыли",
                       labels={'Profit': 'Прибыль', 'count': 'Количество'})

    fig.update_layout(bargap=0.1)

    return fig


@app.callback(
    Output('data-table', 'data'),
    [Input('stored-data', 'data'),
     Input('category-selector', 'value')]
)
def update_table(data, selected_categories):
    if not data:
        return dash.no_update

    df = pd.DataFrame(data)

    if selected_categories:
        if 'Category' in df.columns:
            df = df[df['Category'].isin(selected_categories)]
        elif 'category' in df.columns:
            df = df[df['category'].isin(selected_categories)]

    return df.to_dict('records')


if __name__ == '__main__':
    app.run(debug=True)
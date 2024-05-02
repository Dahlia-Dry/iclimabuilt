from dash import html, dcc
import dash_bootstrap_components as dbc
import datetime

today= datetime.date.today()
start_date = today-datetime.timedelta(days=7)
LAYOUT = html.Div([
    #header
    dbc.Row([
            dbc.Col([html.A(
                        href="https://www.tegnology.dk/",
                        children=html.Img(src='assets/logo.png',style={'width':'100%'}))],width=3),
            dbc.Col([html.H1(children='IClimaBuilt Dashboard')],width=9)],
            style={'padding':10}),
    dbc.Row([dcc.DatePickerRange(
                id='data-range',
                min_date_allowed=datetime.date(2023,6,1),
                max_date_allowed=today,
                start_date=start_date,
                end_date=today
        ),
        dcc.Markdown(id='last-updated',style={'padding':10,'font-size':'10px'})
        ],style={'display':'inline-block','padding':10}),
    dbc.Row([
        html.H2('ΔT vs TEGnology In-Situ Temperature'),
    ],style={'padding':10}),
    dcc.Graph(id='delt-graph'),
    dbc.Row([
        html.H2('Indoor Relative Humidity vs TEGnology In-Situ Relative Humidity'),
    ],style={'padding':10}),
    dcc.Graph(id='irh-graph'),
    dbc.Row([
        html.H2('LivingLabs In-Situ Relative Humidity vs TEGnology In-Situ Relative Humidity'),
    ],style={'padding':10}),
    dcc.Graph(id='isrh-graph'),
    dbc.Row([
        html.H2('Estimate of TEG Output Power vs ΔT'),
    ],style={'padding':10}),
    dcc.Graph(id='power-graph'),
])


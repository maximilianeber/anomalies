import pandas as pd
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
from datetime import datetime

# Load data
df_monthly = pd.read_csv("data/signal_month_returns.csv")

# Clean up date
df_monthly['Day'] = 1
df_monthly['Date'] = pd.to_datetime(df_monthly[['Year', 'Month', 'Day']], errors='coerce')
df_monthly['Date'] = df_monthly['Date'] + pd.tseries.offsets.MonthEnd()
df_monthly.drop(['Day', 'Month', 'Year'], axis=1, inplace=True)

# Get list of anomalies
anomalies = df_monthly.columns.to_list()
anomalies.remove('Date')

# Calculate cumulative returns
df = df_monthly.copy()
df[anomalies] = 1. + df[anomalies] / 100. # gross returns
df[anomalies] = df[anomalies].cumprod(axis=0)


# Define application
app = dash.Dash(__name__)
app.title = 'A Visualization of 143 Stock Market Anomalies'
app.css.append_css({
    "external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"
})


app.layout = html.Div([
    dcc.Markdown('# A Visualization of 143 Stock Market Anomalies'),

    html.Label('Choose anomalies'),
    dcc.Dropdown(
        id='anomaly-selector',
        options=[{'label':a, 'value':a} for a in anomalies],
        value=['Size', 'BM', 'Mom1m'],
        multi=True,
    ),
    html.Br(),
    html.Label('Choose timeframe'),
    dcc.RangeSlider(
        id='year-slider',
        value=[1980, 2018],
        min=1970,
        max=2018,
        step=1,
        marks={i: f"{i}" for i in range(1970, 2020, 5)},
    ),
    html.Br(),
    dcc.Graph(
        id='return-chart',
        config={'displayModeBar': False}),
    html.Br(),
    dcc.Markdown(
        """**Notes:**  
        Data from [Chen and Zimmermann (2019)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2802357)  
        Code on [GitHub](https://github.com/maximilianeber/anomalies)  
        © 2019 [Maximilian Eber](https://www.maximilianeber.com) ([Impressum](https://maximilianeber.com/impressum/))
        """)
])


@app.callback(
    Output('return-chart', 'figure'),
    [Input('anomaly-selector', 'value'),
     Input('year-slider', 'value')],
)
def plot_anomalies(anomalies, year_limits):
    """Plot cumulative returns for chosen anomalies and starting date"""
    df_plot = df[['Date'] + anomalies]
    df_plot = df_plot.loc[df_plot['Date'] > datetime(year_limits[0], 1, 1)]
    df_plot = df_plot.loc[df_plot['Date'] <= datetime(year_limits[1], 1, 1)]
    df_plot[anomalies] = df_plot[anomalies] / df_plot[anomalies].iloc[0] - 1  # Normalize

    def plot_cumreturn(x):
        """Return graph object (lineplot) per anomaly"""
        return go.Scatter(x=df_plot['Date'], y=df_plot[x], mode='lines', name=x)

    comb_cumreturn = [plot_cumreturn(x) for x in anomalies]
    layout = go.Layout(
        title='Cumulative Returns',
        hovermode='closest',
    )
    fig = {'data': comb_cumreturn, 'layout': layout}
    return fig


application = app.server  # Config for AWS EB

if __name__ == '__main__':
    app.run_server(debug=True)
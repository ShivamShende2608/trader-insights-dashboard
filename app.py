import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# =========================================================
# 1. DATA PROCESSING (The Brains)
# =========================================================
try:
    # Load the datasets
    # NOTE: Ensure these file names match exactly what you have in the folder
    df_hist = pd.read_csv('historical_data_compressed.csv')
    df_fg = pd.read_csv('fear_greed_index.csv')

    # Convert Date formats to ensure they match
    # Historical Data uses "Day-Month-Year Hour:Minute" format
    df_hist['Date_Clean'] = pd.to_datetime(df_hist['Timestamp IST'], format='%d-%m-%Y %H:%M', errors='coerce').dt.date
    
    # Fear Greed Data uses "Year-Month-Day"
    df_fg['Date_Clean'] = pd.to_datetime(df_fg['date'], errors='coerce').dt.date

    # Merge the datasets on the Date
    # We use 'inner' join to only keep trades that have a matching sentiment record
    df = pd.merge(df_hist, df_fg, on='Date_Clean', how='inner')

    # Create a "Win" column (1 if profit > 0, else 0) for calculating Win Rate
    df['Win'] = df['Closed PnL'].apply(lambda x: 1 if x > 0 else 0)
    
    print("✅ Data Loaded Successfully!")

except Exception as e:
    print(f"❌ Error Loading Data: {e}")
    # Create an empty dataframe to prevent the app from crashing if files are missing
    df = pd.DataFrame(columns=['Date_Clean', 'classification', 'Closed PnL', 'Win', 'Side', 'Coin'])

# =========================================================
# 2. STYLING CONFIGURATION (The "Web3" Look)
# =========================================================
# We define our CSS styles here as Python dictionaries
STYLES = {
    'body': {
        'background': 'linear-gradient(135deg, #0f0c29, #302b63, #24243e)',
        'min-height': '100vh',
        'font-family': '"Segoe UI", Roboto, Helvetica, Arial, sans-serif',
        'color': '#ffffff',
        'padding': '20px'
    },
    'card': {
        'background': 'rgba(255, 255, 255, 0.05)', # Transparent White
        'border-radius': '15px',
        'padding': '20px',
        'margin-bottom': '20px',
        'box-shadow': '0 8px 32px 0 rgba(0, 0, 0, 0.37)', # Glow effect
        'backdrop-filter': 'blur(8px)', # Glass blur
        'border': '1px solid rgba(255, 255, 255, 0.1)'
    },
    'title': {
        'background': '-webkit-linear-gradient(45deg, #00F260, #0575E6)',
        '-webkit-background-clip': 'text',
        '-webkit-text-fill-color': 'transparent',
        'font-weight': 'bold',
        'font-size': '2.5rem',
        'text-align': 'center',
        'margin-bottom': '10px'
    }
}

# =========================================================
# 3. APP LAYOUT (The Structure)
# =========================================================
app = dash.Dash(__name__)
server = app.server

app.layout = html.Div(style=STYLES['body'], children=[
    
    # --- HEADER ---
    html.Div([
        html.H1("TRADER INTELLIGENCE HUB", style=STYLES['title']),
        html.P("Analyzing Performance vs. Market Sentiment", style={'text-align': 'center', 'opacity': '0.7'})
    ], style={'margin-bottom': '30px'}),

    # --- TOP METRICS ROW ---
    html.Div([
        # Metric 1
        html.Div(style=STYLES['card'], children=[
            html.H4("Total PnL", style={'margin': '0', 'opacity': '0.6'}),
            html.H2(f"${df['Closed PnL'].sum():,.2f}", style={'color': '#00F260' if df['Closed PnL'].sum() > 0 else '#ff4b1f'})
        ], className='three columns'),
        
        # Metric 2
        html.Div(style=STYLES['card'], children=[
            html.H4("Total Trades", style={'margin': '0', 'opacity': '0.6'}),
            html.H2(f"{len(df):,}", style={'color': '#00dbde'})
        ], className='three columns'),

        # Metric 3
        html.Div(style=STYLES['card'], children=[
            html.H4("Win Rate", style={'margin': '0', 'opacity': '0.6'}),
            html.H2(f"{(df['Win'].mean() * 100):.1f}%", style={'color': '#f8ceec'})
        ], className='three columns'),
        
    ], style={'display': 'flex', 'gap': '20px', 'justify-content': 'space-around'}),

    # --- CHARTS ROW 1 ---
    html.Div([
        # Chart: Sentiment vs PnL
        html.Div(style={**STYLES['card'], 'flex': '1'}, children=[
            html.H3("💰 Profit/Loss by Market Sentiment", style={'text-align': 'center'}),
            dcc.Graph(
                id='sentiment-pnl-chart',
                figure=px.box(
                    df, x='classification', y='Closed PnL', color='classification',
                    template='plotly_dark',
                    color_discrete_sequence=px.colors.qualitative.Bold
                ).update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', 
                    plot_bgcolor='rgba(0,0,0,0)',
                    font={'color': 'white'}
                )
            )
        ]),
        
        # Chart: Win Rate by Sentiment
        html.Div(style={**STYLES['card'], 'flex': '1'}, children=[
            html.H3("🎯 Win Rate by Sentiment", style={'text-align': 'center'}),
            dcc.Graph(
                id='win-rate-chart',
                figure=px.bar(
                    df.groupby('classification')['Win'].mean().reset_index(), 
                    x='classification', y='Win', color='Win',
                    title="Likelihood of a Winning Trade",
                    template='plotly_dark',
                    color_continuous_scale='Viridis'
                ).update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', 
                    plot_bgcolor='rgba(0,0,0,0)',
                    font={'color': 'white'},
                    yaxis_tickformat='.0%'
                )
            )
        ])
    ], style={'display': 'flex', 'gap': '20px', 'flex-wrap': 'wrap'}),

    # --- CHARTS ROW 2 ---
    html.Div([
        html.Div(style=STYLES['card'], children=[
            html.H3("📈 Account Growth Over Time", style={'text-align': 'center'}),
            dcc.Graph(
                id='cumulative-pnl-chart',
                figure=px.line(
                    df.sort_values('Date_Clean'), 
                    x='Date_Clean', y=df.sort_values('Date_Clean')['Closed PnL'].cumsum(),
                    template='plotly_dark'
                ).update_traces(
                    line=dict(color='#00F260', width=3)
                ).update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', 
                    plot_bgcolor='rgba(0,0,0,0)',
                    font={'color': 'white'},
                    hovermode="x unified"
                )
            )
        ])
    ])
])

# =========================================================
# 4. RUN SERVER (The Launch Button)
# =========================================================
if __name__ == '__main__':
    app.run(debug=True)
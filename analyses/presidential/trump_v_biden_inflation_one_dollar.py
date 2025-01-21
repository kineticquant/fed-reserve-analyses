import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv
import plotly.graph_objects as go

load_dotenv()

dbname = os.getenv("DB_NAME")
user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")
host = os.getenv("DB_HOST")
port = os.getenv("DB_PORT")

def fetch_data(president_name, index):
    """Fetch data for a given president and index."""
    conn = psycopg2.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port
    )
    
    # Query to get president's term dates
    term_query = f"""
        SELECT start_date, end_date
        FROM presidential_terms
        WHERE president_name = '{president_name}'
    """
    term_df = pd.read_sql_query(term_query, conn)
    start_date = term_df['start_date'].values[0]
    end_date = term_df['end_date'].values[0]
    
    # Query to get CPI data
    cpi_query = """
        SELECT date, cpi
        FROM cpi
        WHERE date BETWEEN %s AND %s
    """
    cpi_df = pd.read_sql_query(cpi_query, conn, params=(start_date, end_date))
    
    # Query to get index data
    index_query = f"""
        SELECT date, {index}
        FROM {index}
        WHERE date BETWEEN %s AND %s
    """
    index_df = pd.read_sql_query(index_query, conn, params=(start_date, end_date))
    
    conn.close()
    
    if 'date' in cpi_df.columns:
        cpi_df['date'] = pd.to_datetime(cpi_df['date'])
    else:
        raise KeyError("The 'date' column is missing from CPI data.")
    
    if 'date' in index_df.columns:
        index_df['date'] = pd.to_datetime(index_df['date'])
    else:
        raise KeyError(f"The 'date' column is missing from {index} data.")
    
    cpi_df.sort_values('date', inplace=True)
    index_df.sort_values('date', inplace=True)
    
    return cpi_df, index_df

def plot_investment_growth(president_name, index_df, cpi_df, index_name):
    """Plot growth of $1 investment for a given president and index."""
    merged_df = pd.merge(index_df, cpi_df, on='date')
    
    merged_df['Adjusted_Index'] = merged_df[index_df.columns[1]] / merged_df['cpi']
    
    merged_df['Investment_Value'] = (1 / merged_df['Adjusted_Index'].iloc[0]) * merged_df['Adjusted_Index']
    
    fig = go.Figure()
    
    # Add investment trace
    fig.add_trace(go.Scatter(
        x=merged_df['date'],
        y=merged_df['Investment_Value'],
        mode='lines',
        name=f'$1 Investment in {index_name}',
        line=dict(color='orange' if index_name == 'DJI' else 'lightblue')
    ))
    
    # Update layout for dark mode with additional styling
    fig.update_layout(
        template='plotly_dark',
        xaxis_title='Date',
        yaxis_title=f'Value of $1 Investment in {index_name}',
        title=f'Growth of $1 Investment ROI Based on {index_name} during {president_name}\'s Presidency',
        legend=dict(x=0, y=1),
        plot_bgcolor='#2c2c2c',
        paper_bgcolor='#2c2c2c',
        annotations=[
            dict(
                x=0.95,
                y=0.01,
                xref='paper',
                yref='paper',
                text='Data by Erie Analytica',
                showarrow=False,
                font=dict(color='white')
            )
        ],
        width=800,
        height=600
    )
    
    fig.show()

biden_cpi_df, biden_dji_df = fetch_data('Joe Biden', 'dji')
plot_investment_growth('Joe Biden', biden_dji_df, biden_cpi_df, 'DJI')

biden_cpi_df, biden_sp500_df = fetch_data('Joe Biden', 'sp500')
plot_investment_growth('Joe Biden', biden_sp500_df, biden_cpi_df, 'S&P500')

trump_cpi_df, trump_dji_df = fetch_data('Donald Trump', 'dji')
plot_investment_growth('Donald Trump', trump_dji_df, trump_cpi_df, 'DJI')

trump_cpi_df, trump_sp500_df = fetch_data('Donald Trump', 'sp500')
plot_investment_growth('Donald Trump', trump_sp500_df, trump_cpi_df, 'S&P500')

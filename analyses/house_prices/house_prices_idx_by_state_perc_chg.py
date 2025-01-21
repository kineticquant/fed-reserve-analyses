from dash import dcc, html
import dash
from dash.dependencies import Input, Output
import pandas as pd
import psycopg2
import plotly.express as px
import plotly.graph_objects as go
import os
from dotenv import load_dotenv

load_dotenv()

dbname = os.getenv("DB_NAME")
user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")
host = os.getenv("DB_HOST")
port = os.getenv("DB_PORT")

conn = psycopg2.connect(
    dbname=dbname,
    user=user,
    password=password,
    host=host,
    port=port
)

# Query to get the most recent data for the percentage change chart
query_percentage = """
    SELECT state, house_price, "4_years", "4_years_percent", 
           "10_years", "10_years_percent", "25_years", 
           "25_years_percent", "all_time", "all_time_percent", 
           president, president_amt, president_percent, date
    FROM state_house_prices
    WHERE date = (SELECT MAX(date) FROM state_house_prices)
"""

df_percentage = pd.read_sql(query_percentage, conn)

# Query to get all data for the president-specific chart
query_president = """
    SELECT state, house_price, "4_years", "4_years_percent", 
           "10_years", "10_years_percent", "25_years", 
           "25_years_percent", "all_time", "all_time_percent", 
           president, president_amt, president_percent, date
    FROM state_house_prices
"""

df_president = pd.read_sql(query_president, conn)

# Ensure 'date' column is in datetime format
df_percentage['date'] = pd.to_datetime(df_percentage['date'])
df_president['date'] = pd.to_datetime(df_president['date'])

# Extract year from 'date' column
df_percentage['year'] = df_percentage['date'].dt.year
df_president['year'] = df_president['date'].dt.year

# Get min and max years for "All Time" title
min_year_query = """
    SELECT EXTRACT(YEAR FROM MIN(date)) AS min_year
    FROM state_house_prices
"""
max_year_query = """
    SELECT EXTRACT(YEAR FROM MAX(date)) AS max_year
    FROM state_house_prices
"""

min_year = pd.read_sql(min_year_query, conn).iloc[0]['min_year']
max_year = pd.read_sql(max_year_query, conn).iloc[0]['max_year']

# Convert years to integers
min_year = int(min_year)
max_year = int(max_year)

# Get unique president names for dropdown, filtered by date
presidents_query = """
    SELECT DISTINCT president
    FROM state_house_prices
    WHERE president IS NOT NULL
"""
df_presidents = pd.read_sql(presidents_query, conn)['president'].dropna().unique()
conn.close()

# Create Dash app
app = dash.Dash(__name__)

# Layout
app.layout = html.Div([
    # Top
    html.Div([
        html.H1("House Price Changes by State"),
        html.Div([
            html.H2("Percentage Change Chart"),
            dcc.Dropdown(
                id='percentage-dropdown',
                options=[
                    {'label': '4 Years Percent Change', 'value': '4_years_percent'},
                    {'label': '10 Years Percent Change', 'value': '10_years_percent'},
                    {'label': '25 Years Percent Change', 'value': '25_years_percent'},
                    {'label': 'All Time Percent Change', 'value': 'all_time_percent'}
                ],
                value='4_years_percent'  # Default
            ),
            dcc.Graph(id='percentage-heatmap')
        ], style={'margin-bottom': '40px'}),  # Add margin between sections

        html.Hr(),  # Horizontal div

        # Bottom 
        html.Div([
            html.H2("President Data Chart"),
            dcc.Dropdown(
                id='president-dropdown',
                options=[{'label': 'Select President', 'value': ''}] + [{'label': name, 'value': name} for name in df_presidents],
                value=''  # Default value for dropdown (no president selected)
            ),
            dcc.Graph(id='president-heatmap')
        ])
    ])
])

def get_text_color(value):
    if value is None:
        return 'black'
    #elif value > 55:
    #    return 'white'
    else:
        return 'black'

@app.callback(
    [Output('percentage-heatmap', 'figure'),
     Output('president-heatmap', 'figure')],
    [Input('percentage-dropdown', 'value'),
     Input('president-dropdown', 'value')]
)
def update_charts(percentage_selection, president_selection):
    fig_percentage = go.Figure()
    fig_president = go.Figure()

    # Update Percentage Change Chart
    if percentage_selection in ['4_years_percent', '10_years_percent', '25_years_percent', 'all_time_percent']:
        if percentage_selection == '4_years_percent':
            end_date = df_percentage['date'].max()
            start_date = end_date - pd.DateOffset(years=4)
            title_text = f'House Price Change - 4 Years Percent Change ({start_date.year} to {end_date.year})'
            df_filtered = df_percentage[(df_percentage['date'] >= start_date) & (df_percentage['date'] <= end_date)]
        elif percentage_selection == '10_years_percent':
            end_date = df_percentage['date'].max()
            start_date = end_date - pd.DateOffset(years=10)
            title_text = f'House Price Change - 10 Years Percent Change ({start_date.year} to {end_date.year})'
            df_filtered = df_percentage[(df_percentage['date'] >= start_date) & (df_percentage['date'] <= end_date)]
        elif percentage_selection == '25_years_percent':
            end_date = df_percentage['date'].max()
            start_date = end_date - pd.DateOffset(years=25)
            title_text = f'House Price Change - 25 Years Percent Change ({start_date.year} to {end_date.year})'
            df_filtered = df_percentage[(df_percentage['date'] >= start_date) & (df_percentage['date'] <= end_date)]
        elif percentage_selection == 'all_time_percent':
            start_date = df_percentage['date'].min()
            end_date = df_percentage['date'].max()
            title_text = f'House Price Change - All Time Percent Change ({min_year} to {max_year})'
            df_filtered = df_percentage  # No date filtering needed for all-time data
        
        color_column = percentage_selection  # Use the selected percentage column for color
        
        min_value = df_filtered[color_column].min()
        max_value = df_filtered[color_column].max()
        
        tickvals = [min_value, 0, max_value]
        ticktext = [f"{min_value:.2f}%", '0%', f"{max_value:.2f}%"]
        
        fig_percentage = px.choropleth(
            df_filtered,
            locations="state",
            locationmode="USA-states",
            color=color_column,
            scope="usa",
            color_continuous_scale='Blues',  # Change this to 'Cividis', 'Plasma', 'Inferno', or 'Blues' if preferred
            labels={color_column: f'House Price Change ({color_column.replace("_", " ").title()})'}
        )
        
        text_labels = df_filtered[color_column].apply(lambda x: f"{x:.2f}%" if x is not None else 'N/A')
        for i, state in enumerate(df_filtered['state']):
            value = df_filtered[color_column].iloc[i]
            text_color = get_text_color(value)
            fig_percentage.add_trace(go.Scattergeo(
                locations=[state],
                locationmode="USA-states",
                text=[text_labels.iloc[i]],
                mode='text',
                showlegend=False,
                textfont=dict(size=16, color=text_color),
                textposition='middle center'  # Adjust text position to reduce overlap
            ))
        
        fig_percentage.update_layout(
            title_text=title_text,
            geo=dict(showcoastlines=True),
            coloraxis_colorbar=dict(
                title='Percentage Change',
                tickvals=tickvals,
                ticktext=ticktext,
                len=0.8,  # Set length of color bar (fraction of plot height)
                thickness=20  # Fixed thickness of color bar
            ),
            margin=dict(l=0, r=100, t=40, b=0),  # Adjust margins to accommodate the color bar
            width=2350,
            height=1850,
            #plot_bgcolor='lightgray',  # Change plotting area background
            #paper_bgcolor='lightgray'  
        )
    
    if president_selection:
        df_filtered = df_president[df_president['president'] == president_selection]
        
        min_value = df_filtered["president_percent"].min()
        max_value = df_filtered["president_percent"].max()
        
        tickvals = [min_value, 0, max_value]
        ticktext = [f"{min_value:.2f}%", '0%', f"{max_value:.2f}%"]
        
        fig_president = px.choropleth(
            df_filtered,
            locations="state",
            locationmode="USA-states",
            color="president_percent",
            scope="usa",
            color_continuous_scale='Blues',  # Change this to 'Cividis', 'Plasma', 'Inferno', or 'Blues' if preferred
            labels={"president_percent": f'{president_selection} Percent Change'}
        )
        
        text_labels = df_filtered['president_percent'].apply(lambda x: f"{x:.2f}%" if x is not None else 'N/A')
        for i, state in enumerate(df_filtered['state']):
            value = df_filtered['president_percent'].iloc[i]
            text_color = get_text_color(value)
            fig_president.add_trace(go.Scattergeo(
                locations=[state],
                locationmode="USA-states",
                text=[text_labels.iloc[i]],
                mode='text',
                showlegend=False,
                textfont=dict(size=16, color=text_color),
                textposition='middle center'  # Adjust text position to reduce overlap
            ))
        
        fig_president.update_layout(
            title_text=f'House Price Change During {president_selection}\'s Term',
            geo=dict(showcoastlines=True),
            coloraxis_colorbar=dict(
                title='Percentage Change',
                tickvals=tickvals,
                ticktext=ticktext,
                len=0.8,  # Set length of color bar (fraction of plot height)
                thickness=20  # Fixed thickness of color bar
            ),
            margin=dict(l=0, r=100, t=40, b=0),  # Adjust margins to accommodate the color bar
            width=2350,
            height=1850
        )
    
    return fig_percentage, fig_president

if __name__ == '__main__':
    app.run_server(debug=True)

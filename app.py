import dash
from dash import html, dcc
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.graph_objects as go

# Initialize the Dash app
app = dash.Dash(__name__)

# Sample DataFrame - replace with your data
ffinal = pd.read_csv('data/final.csv')
final = ffinal.query('deposit < 13000 & expected_time < 90').copy().sort_values('번호')

# Initial map figure
fig = go.Figure()

map_trace = go.Scattermapbox(
    lat=final.x,
    lon=final.y,
    mode='markers+text',
    marker=go.scattermapbox.Marker(
        size=20,
        color=final['deposit_m2'],
        colorscale='Viridis_r',
        showscale=True
    ),
    text=final['번호'].astype(str),
    hoverinfo='text'
)

fig.add_trace(map_trace)

fig.update_traces(
    hovertext=final.apply(
        lambda row: (
            f"<b>번호: {row['번호']}</b><br>"
            f"주소: {row['주소']}<br><br>"
            f"가장가까운역: {row['near_station']}"
        ), axis=1
    ),
    hoverinfo='text'
)

fig.update_layout(
    mapbox=dict(
        accesstoken='mapbox_token',
        style='open-street-map',
        zoom=9,
        center=dict(lat=final.x.mean(), lon=final.y.mean())
    ),
    margin={"r": 0, "t": 0, "l": 0, "b": 0}
)

# Define the layout with two columns side by side
app.layout = html.Div([
    # First column for the map
    html.Div([
        html.H1(children='Map and Controls'),
        html.Div([html.Label("건물번호"), 
                  dcc.Dropdown(
            id='image-dropdown',
            options=[
                {'label': f'{num:03d}', 'value': f'{num:03d}'}
                for num in final['번호'].values
            ],
            value='007',
            clearable=False,
            style={'width': '150px', 'display': 'inline-block', 'marginLeft': '20px', 'verticalAlign': 'top'}
        ),
        html.Label("표시색상"),
                  dcc.Dropdown(
                id='color-data-dropdown',
                options=[
                    {'label': '보증금', 'value': 'deposit'},
                    {'label': '인접역까지 거리', 'value': 'distanceM_near_station'},
                    {'label': '신청자수', 'value': '신청자수'},
                    {'label': 'm2당 보증금', 'value': 'deposit_m2'}
                ],
                value='deposit_m2',  # Default value for color bar data
                clearable=False,
                style={'width': '180px', 'display': 'inline-block', 'marginLeft': '20px', 'verticalAlign': 'top'}) # Inline style with margin
        ], style={'marginBottom': '10px'}),  # Add some margin below for spacing

        html.Div([
            dcc.RadioItems(
                id='map-style-radio',
                options=[
                    {'label': 'Open Street Map', 'value': 'open-street-map'},
                    {'label': 'Carto Positron', 'value': 'carto-positron'},
                    {'label': 'Carto Darkmatter', 'value': 'carto-darkmatter'},
                    {'label': 'Stamen Terrain', 'value': 'stamen-terrain'}
                ],
                value='open-street-map',
                inline=True,
                style={'display': 'inline-block', 'verticalAlign': 'top'}  # Inline style
            )
            
        ], style={'marginBottom': '10px'}),
        
        dcc.Graph(id='mapbox-graph', figure=fig, style={'height': '700px'}),

        html.Label("Zoom Level"),
        dcc.Slider(
            id='zoom-slider',
            min=7,
            max=15,
            value=9,
            marks={i: str(i) for i in range(7, 16)},
            step=1
        )
    ], style={'width': '60%', 'display': 'inline-block', 'verticalAlign': 'top'}),  # Map Column 70%
    
    # Second column for the image and dropdown
    html.Div([
        html.H1("평면구조도"),
        html.Div(id='image-container', children=[
            html.Img(id='dynamic-image', style={'width': '100%', 'height': '300px'})  # Fixed size for the images
        ]),
        
        # New Div to display property details
        html.Div(id='property-details', style={'padding-top': '20px', 'font-size': '18px', 'border': '1px solid #ddd', 'padding': '10px', 'backgroundColor': '#f9f9f9'})  # Style as needed
    ], style={'width': '35%', 'display': 'inline-block', 'padding-left': '2%', 'verticalAlign': 'top'})  # Image Column 30%
])

# Callback to update the map's color and style without recreating the entire figure
@app.callback(
    Output('mapbox-graph', 'figure'),
    [Input('map-style-radio', 'value'),
     Input('color-data-dropdown', 'value'),
     Input('zoom-slider', 'value')]
     )

def update_map(style, color_column, zoom_level):
    # Update the color of the markers dynamically
    fig.data[0].marker.color = final[color_column]

    # Update the map style and zoom level
    fig.update_layout(
        mapbox_style=style,
        mapbox_zoom=zoom_level
    )

    return fig


# Callback to update the image in the second column based on dropdown selection
@app.callback(
    [Output('dynamic-image', 'src'),
     Output('property-details', 'children')],
    Input('image-dropdown', 'value')
)
def update_image_and_details(selected_value):
    # Map the selected value to corresponding image URLs
    image_urls = {
        f'{num:03d}':img_url for idx, num, img_url in final.filter(regex = '번호|img').itertuples()
    }

    selected_row = final[final['번호'] == int(selected_value)]

    if not selected_row.empty:
        row = selected_row.iloc[0]
        details = [
            html.P(f"번호: {row['번호']}"),
            html.P(f"주소: {row['주소']}"),
            html.P(f"주택유형: {row['주택유형']}"),
            html.P(f"전용면적: {round(row['m2'] / 3.30579, 1)}평"),
            html.P(f"보증금: {int(row['deposit'])}만원"),
            html.P(f"가장 가까운 역까지 거리: {row['near_station']}까지 {int(row['distanceM_near_station'])}m"),
            html.P(f"회사까지 예상 소요 시간: {round(row['expected_time'], 1)}분"),
            html.P(f"신청자수: {row['신청자수']}명")
        ]
    else:
        details = [html.P("No details available for this selection.")]

    return image_urls.get(selected_value, ''), details


server = app.server

# Run the app
# if __name__ == '__main__':
    # app.run_server(debug=True)

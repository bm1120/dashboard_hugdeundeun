import dash
from dash import html, dcc
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.graph_objects as go

# Initialize the Dash app
app = dash.Dash(__name__)

# Sample DataFrame - replace with your data
ffinal = pd.read_csv('final_241007.csv')
final = ffinal.query('deposit < 13000 & expected_time < 90').copy()

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
            f"주택유형: {row['주택유형']}<br>"
            f"전용면적: {round(row['m2'] / 3.30579, 1)}평<br>"
            f"보증금: {int(row['deposit'])}만원<br>"
            f"가장가까운역까지 거리: {row['near_station']}까지 {int(row['distanceM_near_station'])}m<br>"
            f"회사까지 예상 소요 시간: {round(row['expected_time'], 1)}분"
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
        dcc.RadioItems(
            id='map-style-radio',
            options=[
                {'label': 'Open Street Map', 'value': 'open-street-map'},
                {'label': 'Carto Positron', 'value': 'carto-positron'},
                {'label': 'Carto Darkmatter', 'value': 'carto-darkmatter'},
                {'label': 'Stamen Terrain', 'value': 'stamen-terrain'}
            ],
            value='open-street-map',
            inline=True
        ),
        dcc.Graph(id='mapbox-graph', figure=fig),
        html.Label("Zoom Level"),
        dcc.Slider(
            id='zoom-slider',
            min=7,
            max=15,
            value=10,
            marks={i: str(i) for i in range(7, 16)},
            step=1
        )
    ], style={'width': '70%', 'display': 'inline-block', 'verticalAlign': 'top'}),  # Map Column 70%

    # Second column for the image and dropdown
    html.Div([
        html.H1("평면구조도"),
        dcc.Dropdown(
            id='image-dropdown',
            options=[
                {'label': '007', 'value': '007'},
                {'label': '010', 'value': '010'},
                {'label': '018', 'value': '018'},
                {'label': '054', 'value': '054'},
                {'label': '065', 'value': '065'}
            ],
            value='007',
            clearable=False,
        ),
        html.Div(id='image-container', children=[
            html.Img(id='dynamic-image', style={'width': '100%', 'height': '300px'})  # Fixed size for the images
        ])
    ], style={'width': '28%', 'display': 'inline-block', 'padding-left': '2%', 'verticalAlign': 'top'})  # Image Column 30%
])

# Consolidated callback to handle map style, zoom changes, and dropdown location selection
@app.callback(
    Output('mapbox-graph', 'figure'),
    [Input('map-style-radio', 'value'),
     Input('zoom-slider', 'value'),
     Input('image-dropdown', 'value')],
    [State('mapbox-graph', 'relayoutData'),
     State('mapbox-graph', 'figure')]
)
def update_map(style, zoom_level, selected_value, relayout_data, current_fig):
    # Update map style
    current_fig['layout']['mapbox'].update(style=style)
    
    # Update map zoom level
    if relayout_data and 'mapbox.center' in relayout_data:
        center = relayout_data['mapbox.center']
    else:
        center = current_fig['layout']['mapbox']['center']
    
    current_fig['layout']['mapbox'].update(zoom=zoom_level, center=center)

    # Update map center based on selected dropdown option
    if selected_value:
        selected_row = final[final['번호'] == int(selected_value)]
        if not selected_row.empty:
            lat = selected_row['x'].values[0]
            lon = selected_row['y'].values[0]
            current_fig['layout']['mapbox'].update(center=dict(lat=lat, lon=lon))

    return current_fig

# Callback to update the image in the second column based on dropdown selection
@app.callback(
    Output('dynamic-image', 'src'),
    Input('image-dropdown', 'value')
)
def update_image(selected_value):
    # Map the selected value to corresponding image URLs (replace with your actual image paths)
    image_urls = {
        '007': 'https://www.khug.or.kr/updata/khgc/khgccms/cms/upload/1264/20241002183532907.jpg',
        '010': 'https://www.khug.or.kr/updata/khgc/khgccms/cms/upload/1264/20241002182133316.jpg',
        '018': 'https://www.khug.or.kr/updata/khgc/khgccms/cms/upload/1264/20240926165705645.png',
        '054': 'https://www.khug.or.kr/updata/khgc/khgccms/cms/upload/1264/20240926173347688.jpg',
        '065': 'https://www.khug.or.kr/updata/khgc/khgccms/cms/upload/1264/20241002183726279.jpg'
    }
    return image_urls.get(selected_value, '')

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)

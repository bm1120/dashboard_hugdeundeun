import dash
from dash import html, dcc
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.graph_objects as go

# Initialize the Dash app
app = dash.Dash(__name__)

# Sample DataFrame - replace with your data
ffinal = pd.read_csv('data/final.csv')
# final = ffinal.query('deposit < 13000 & expected_time < 90').copy().sort_values('번호')
final = ffinal.copy().sort_values('번호')


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
        # Input field for filtering the data based on deposit
        html.Div([
            html.Label("최대 보증금(만원)", style={'marginRight': '10px'}),
            dcc.Input(id='min-deposit-input', type='number', value=30000, style={'marginBottom': '20px'})
        ]),  # Default to 0

        html.Label("최대 통근시간(분)", style={'marginRight': '10px'}),
        dcc.Input(id='max-time-input', type='number', value=90, style={'marginBottom': '20px'}),  # Default to 0
        
        html.Div([html.Label("건물 표시색상"),
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
                style={'width': '150px', 'display': 'inline-block', 'marginLeft': '5px', 'verticalAlign': 'top'}) # Inline style with margin
        ], style={'marginBottom': '10px', 'float': 'right'}),  # Add some margin below for spacing

        
        dcc.Graph(id='mapbox-graph', figure=fig, style={'height': '700px'}),
        
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
            
        ], style={'marginBottom': '10px'})
    ], style={'width': '60%', 'display': 'inline-block', 'verticalAlign': 'top'}),  # Map Column 70%
    
    # Second column for the image and dropdown
    html.Div([
        html.H1("평면구조도"),
        html.Div([html.Label("건물번호"), 
                  dcc.Dropdown(
            id='image-dropdown',
            options=[
                {'label': f'{num:03d}', 'value': f'{num:03d}'}
                for num in final['번호'].values
            ],
            value='001',
            clearable=False,
            style={'width': '100px', 'display': 'inline-block', 'marginLeft': '20px', 'verticalAlign': 'top'}
        )], style={'marginBottom': '10px',  'textAlign':'right'}),
        html.Div(id='image-container', children=[
            html.Img(id='dynamic-image', style={'width': '100%', 'height': '400px'})  # Fixed size for the images
        ]),
        
        # New Div to display property details
        html.Div(id='property-details', style={'padding-top': '20px', 'font-size': '18px', 'border': '1px solid #ddd', 'padding': '10px', 'backgroundColor': '#f9f9f9'})  # Style as needed
    ], style={'width': '35%', 'display': 'inline-block', 'padding-left': '2%', 'verticalAlign': 'top'})  # Image Column 30%
])

# Callback to update the map's color, style, maintain zoom level, and center on selected building
@app.callback(
    Output('mapbox-graph', 'figure'),
    [Input('map-style-radio', 'value'),
     Input('color-data-dropdown', 'value'),
     Input('min-deposit-input', 'value'),
     Input('max-time-input', 'value'),
     Input('image-dropdown', 'value')],  # New input to track selected building
    [State('mapbox-graph', 'relayoutData')]  # Track the current zoom level and center
)
def update_map(style, color_column, max_deposit, max_time, selected_building, relayout_data):
    # Filter the data based on the deposit and time inputs
    filtered_data = final[(final['deposit'] <= max_deposit) & (final['expected_time'] <= max_time)]
    
    # Update the map trace with the filtered data
    map_trace = go.Scattermapbox(
        lat=filtered_data.x,
        lon=filtered_data.y,
        mode='markers+text',
        marker=go.scattermapbox.Marker(
            size=20,
            color=filtered_data[color_column],
            colorscale='Viridis_r',
            showscale=True
        ),
        text=filtered_data['번호'].astype(str),
        hoverinfo='text'
    )

    fig = go.Figure(data=[map_trace])

    # Update hover text with building details
    fig.update_traces(
        hovertext=filtered_data.apply(
            lambda row: (
                f"<b>번호: {row['번호']}</b><br>"
                f"주소: {row['주소']}<br><br>"
                f"가장 가까운 역: {row['near_station']}"
            ), axis=1
        ),
        hoverinfo='text'
    )

    # Check if relayoutData exists and contains zoom and center information
    if relayout_data and 'mapbox.zoom' in relayout_data:
        current_zoom = relayout_data['mapbox.zoom']
        current_center = relayout_data.get('mapbox.center', {'lat': filtered_data.x.mean(), 'lon': filtered_data.y.mean()})
    else:
        # Use default zoom and center if no user interaction has occurred
        current_zoom = 9
        current_center = {'lat': filtered_data.x.mean(), 'lon': filtered_data.y.mean()}

    # If a building is selected, center the map on its coordinates
    if selected_building:
        selected_row = filtered_data[filtered_data['번호'] == int(selected_building)]
        if not selected_row.empty:
            current_center = {
                'lat': selected_row['x'].values[0],  # Latitude of the selected building
                'lon': selected_row['y'].values[0]   # Longitude of the selected building
            }

    # Update the layout with the style, zoom, and center
    fig.update_layout(
        mapbox=dict(
            accesstoken='mapbox_token',
            style=style,
            zoom=current_zoom,  # Preserve the current zoom level
            center=current_center  # Center the map on the selected building or current center
        ),
        margin={"r": 0, "t": 0, "l": 0, "b": 0}
    )

    return fig


# Callback to update the image in the second column based on dropdown selection
@app.callback(
    [Output('dynamic-image', 'src'),
     Output('property-details', 'children')],
    Input('image-dropdown', 'value')
)
def update_image_and_details(selected_value):
    # If no building is selected (i.e., selected_value is None), return placeholders
    if selected_value is None:
        return '', [html.P("No details available for this selection.")]

    try:
        # Map the selected value to corresponding image URLs
        image_urls = {f'{num:03d}': img_url for idx, num, img_url in final.filter(regex='번호|img').itertuples()}

        # Convert the selected value to an integer for comparison
        selected_row = final[final['번호'] == int(selected_value)]

        # Check if the selected row exists
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

    except Exception as e:
        # Return empty image and error message in case of failure
        return '', [html.P(f"Error: {str(e)}")]


# Callback to update the building number dropdown and its value based on filtered data
@app.callback(
    [Output('image-dropdown', 'options'),
     Output('image-dropdown', 'value')],
    [Input('min-deposit-input', 'value'),
     Input('max-time-input', 'value')],
    [State('image-dropdown', 'value')]  # Track the current selected value
)
def update_building_number_options(max_deposit, max_time, current_value):
    # Filter the data based on the deposit and time inputs
    filtered_data = final[(final['deposit'] <= max_deposit) & (final['expected_time'] <= max_time)]

    # Convert the '번호' column to integers to ensure proper formatting
    filtered_data['번호'] = filtered_data['번호'].astype(int)

    # Generate the list of building numbers as options for the dropdown, formatted to 3 digits
    options = [{'label': f'{num:03d}', 'value': f'{num:03d}'} for num in filtered_data['번호']]

    # If no options are available after filtering, return an empty dropdown and value None
    if not options:
        return [], None

    # Check if the current value is still valid after filtering
    if current_value in [opt['value'] for opt in options]:
        value = current_value  # Keep the current value if it's still valid
    else:
        value = options[0]['value']  # Otherwise, reset to the first available option

    return options, value



server = app.server

# # Run the app
# if __name__ == '__main__':
#     app.run_server(host='0.0.0.0', port=8050, debug=True)

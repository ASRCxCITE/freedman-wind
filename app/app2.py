import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State

import plotly.graph_objects as go
from plotly.subplots import make_subplots

import datetime as dt
import xarray as xr
import wrf as wrf
import netCDF4 as nc
import pandas as pd
import glob
import numpy as np
from matplotlib import cm
import matplotlib.colors as mplcol

import cartopy.io.shapereader as shpreader
from shapely.geometry import Point

from rasterio import features
from affine import Affine
import requests
import json


# -- Configuration Variables --#
mapbox_token = "pk.eyJ1IjoibnNjaGlyYWxkaSIsImEiOiJjanoxOXlraTMwY3RyM2hzMDdhM2RxZGk2In0.3SgrGa7NM-r-MFVHl1lDmw"
counties = {
    "119": "Westchester",
    "081": "Queens",
    #'061': 'Manhattan',
    "085": "Staten Island",
    "005": "Bronx",
    "047": "Brooklyn",
}
ZOOM=7
CENTER_LAT=41.019801
CENTER_LONG=-73.723068
# -- global variables --#
shp = shpreader.Reader("assets/tl_2018_us_county")
polys = {}
for r in shp.records():
    if r.attributes["STATEFP"] == "36" and r.attributes["COUNTYFP"] in counties.keys():
        polys[counties[r.attributes["COUNTYFP"]]] = r.geometry

# power_lines=requests.get('https://opendata.arcgis.com/datasets/70512b03fe994c6393107cc9946e5c22_0.geojson')
# power_lines=power_lines.json()
# hour_checklist = [{'label':'All','value':0}]
# hour_checklist = [{'label':k+1,'value':k+1} for k in range(120)]
# print(hour_checklist)

                                     

# -- Specify layout components --#


body = dbc.Container(
    [
        dbc.Container(
            [
                dbc.Row(
                    [
                        html.H3("Forecast as of "+str(dt.datetime.today().strftime("%b %d, %Y %H:%M"))),
                    ],
                    className="p-2",
                ),
                dbc.Row(
                    [
                        dbc.Col([
                            html.Div([
                            html.H4("Forecast Hours:"),],style={'width':'auto'}),
                            html.Div([
                                html.A("Note increased fetch time for more hours.")
                            ],style={'fontSize':9,'width':'auto'})
                        ],style={},width='auto'),
                        dbc.Col([
                            dbc.Row([
                                dcc.RadioItems(
                                    id="selected-hours1",
                                    options=[{'label':'All (120)','value':0},
                                             {'label':'Every 3','value':1},
                                             {'label':'Every 6','value':2},
                                             {'label':'Every 12','value':3},
                                             {'label':'Custom','value':4},
                                            ],
                                    value=2,
                                    labelStyle={'display': 'inline-block', 'paddingRight':'10px'}),
                                dbc.Button("Fetch Data", id="hour-button", size='sm'),
                            ],style={'marginLeft':5,'marginRight':5},justify='start'),    
                            dbc.Row([
                                html.Div([
                                    dcc.Checklist(
                                        id="selected-hours2",
                                        options=[{'label':k+1,'value':k+1} for k in range(120)],
                                        value=[1,10],
                                        labelStyle={"vertical-align":"middle"},
                                        style={"display":"inline-flex", 
                                               "flex-wrap":"wrap", 
                                               "justify-content":"space-between"}
                                    ),
                                ],style={'marginLeft':5,'width':'50%',
                                         'max-height':'100px','overflow':'scroll'})
                            ],style={},justify='center'),  
                        ],style={},align='left'),
                    ],style={'width':'100%'},
                ),
                # dbc.Progress(id="progress",value="0",animated=True),
                dcc.Loading(
                    id="data-loading",
                    children=[dcc.Store(id="wind-data")],
                    fullscreen=True,
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            dcc.Markdown(
                                """
                Maxmium wind speed observed over a selected date window.
                """
                            )
                        ),
                        dbc.Col(
                            html.P(
                                """Choose the box selector on the top right of the map, select a box,
                 and a line chart of the mean wind speed (mph) over the box will populate.
                """
                            )
                        ),
                    ],
                    className="d-flex justify-content-center pt-1 w-100",
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            dcc.RangeSlider(
                                id="fdate",
                                min=0,
                                max=73,
                                step=1,
                                allowCross=False,
                                value=[0, 4],
                                pushable=4,
                                updatemode="mouseup",
                            ),
                            width=9,
                        ),
                        dbc.Col(dbc.Button("Update Plot!", id="button")),
                    ],
                    className="d-flex justify-content-center pt-4 w-100",
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            dcc.Loading(
                                id="loading-animation",
                                children=[
                                    dcc.Graph(
                                        id="geoanimation",
                                        figure=dict(
                                            layout=dict(
                                                mapbox=dict(
                                                    accesstoken=mapbox_token,
                                                    center=dict(
                                                        lon=CENTER_LONG, lat=CENTER_LAT
                                                    ),
                                                    zoom=ZOOM,
                                                    style="dark",
                                                ),
                                                paper_bgcolor="#303030",
                                                margin=dict(l=0, r=0, t=0, b=0),
                                            )
                                        ),
                                    )
                                ],
                            )
                        ),
                        dbc.Col(
                            dcc.Loading(
                                id="loading-line",
                                children=[
                                    dcc.Graph(
                                        id="line-plot",
                                        figure=dict(
                                            layout=dict(
                                                title="Click on a Polygon",
                                                paper_bgcolor="#303030",
                                                plot_bgcolor="#4a4a4a",
                                                font=dict(color="white"),
                                                yaxis=dict(title="mph")
                                                # margin=dict(t=30,b=40,l=20,r=20)
                                            )
                                        ),
                                    )
                                ],
                            )
                        ),
                    ],
                    className="d-flex justify-content-center pt-4 w-100",
                ),
                html.Hr(),
            ]
        )
    ],
    fluid=True,
)

# -- Initialize the flask application --#
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY, dbc.themes.GRID])
app.layout = html.Div([body])
app.title = "ConEd WindView"
server = app.server

# Define callback functions
@app.callback(
    [Output("wind-data", "data"), Output("fdate", "marks")],
    [Input("hour-button", "n_clicks")],
    [State("selected-hours1","value")],
    [State("wind-data", "data")],
)
def load_data(click, hours, data):

    print("Loading Data",click,hours)
    hour_button_click = click
    response = requests.get("http://169.226.181.187:7006/")
    res = response.json()
    with open(res['filename'],'r') as f:
        json_data = json.load(f)

        return (
            json_data['gust'],
            json_data['marks']
        )
    
@app.callback(Output('selected-hours2', 'labelStyle'),
              Input('selected-hours1', 'value'))
def forecast_hours(value):
    if value == 4:
        return {'display':'inline-block'}
    else: return {'display':'none'}

@app.callback(
    Output("line-plot", "figure"),
    [
        Input("wind-data", "data"),
        Input("geoanimation", "selectedData"),
        Input("button", "n_clicks"),
    ],
    [State("fdate", "value")],
)
def plot_line(data, points, n, dateind):
#     print(data,points,n,dateind)

    if points and data and dateind:
        # print(points['range']['mapbox'][1][1],points['range']['mapbox'][0][1])
        # print(points['range']['mapbox'][0][0],points['range']['mapbox'][1][0])
#         print(dateind[0],dateind[-1])
        
        df = (
            xr.DataArray.from_dict(data)
            .isel(Time=slice(dateind[0], dateind[-1]))
            .sel(
                south_north=slice(
                    points["range"]["mapbox"][1][1], points["range"]["mapbox"][0][1]
                ),
                west_east=slice(
                    points["range"]["mapbox"][0][0], points["range"]["mapbox"][1][0]
                ),
            )
            .max(["south_north", "west_east"])
        )
#         print(df.Time.values)
        data = dict(
            type="scatter",
            x=df.Time.values,#pd.to_datetime(df.Time.values).strftime("%m/%d %H:%M"),
            y=df.values,
            line=dict(color="orange"),
        )
        layout = dict(
            hovermode="closest",
            title="Maximum Wind Speed inside Box",
            yaxis=dict(title="mph", nticks=9, range=[0, 80], gridcolor="#d3d3d3"),
            xaxis=dict(nticks=10, gridcolor="#d3d3d3"),
            paper_bgcolor="#303030",
            plot_bgcolor="#4a4a4a",
            font=dict(color="white"),
        )
        return dict(data=[data], layout=layout)
    else:

        layout = dict(
            hovermode="closest",
            title="Average Wind Speed over Selected Box",
            yaxis=dict(title="mph", nticks=9, range=[0, 80], gridcolor="#d3d3d3"),
            xaxis=dict(nticks=10, gridcolor="#d3d3d3"),
            paper_bgcolor="#303030",
            plot_bgcolor="#4a4a4a",
            font=dict(color="white"),
        )

        return dict(data=[], layout=layout)


@app.callback(
    Output("geoanimation", "figure"),
    [
#         Input("selected-date", "date"),
        Input("wind-data", "data"),
        Input("button", "n_clicks"),
    ],
    [State("fdate", "value"), State("geoanimation", "selectedData")],
)
def plot_geo_animation(data, n, dateind, points):

    geo_layout = dict(
        mapbox=dict(
            accesstoken=mapbox_token,
            center=dict(lon=CENTER_LONG, lat=CENTER_LAT),
            zoom=ZOOM,
            style="dark",
            layers=[],
        ),
        plot_bgcolor="#303030",
        paper_bgcolor="#303030",
        margin=dict(l=0, r=0, t=0, b=0),
        dragmode="select",
    )

    if data and dateind:
        # data to xarray
        df = (
            xr.DataArray.from_dict(data)
            .isel(Time=slice(dateind[0], dateind[-1]))
            .max("Time")
            .coarsen(south_north=3, west_east=3, boundary="pad")
            .max()
        )

        # Set up Colors
        bins = np.arange(0, 61, 5)
        norm = mplcol.Normalize(bins[0], bins[-1])
        colors = cm.viridis(norm(bins))

        annotations = [
            dict(
                showarrow=False,
                # align = 'right',
                text="<b>MPH</b>",
                bgcolor="#EFEFEE",
                x=0.90,
                y=0.915,
            )
        ]

        for i in range(0, len(colors) - 1):
            # color = cm[bin]
            annotations.append(
                dict(
                    arrowcolor=mplcol.rgb2hex(colors[i]),
                    text=("{:1.1f}").format(bins[i]),
                    height=21,
                    x=0.95,
                    y=0.85 - (i / 20),
                    ax=-55,
                    ay=0,
                    arrowwidth=23,
                    arrowhead=0,
                    bgcolor="#EFEFEE",
                )
            )

        geo_layout["annotations"] = annotations

        # Get the max
        x, y = np.meshgrid(df.west_east.values, df.south_north.values)
        gridbox_cind = np.digitize(df.values, bins)

        data = [
            dict(
                type="scattermapbox",
                lon=x.flatten(),
                lat=y.flatten(),
                text=["{0:.1f} mph".format(i) for i in df.values.flatten()],
                hoverinfo="text",
                mode="none",
            )
        ]

        # set up geosjon
        geoJSON = [
            {"type": "FeatureCollection", "features": []} for i in range(len(colors))
        ]

        # each "color" is its own geojson layer for plotly. Loop of lat/lon and create gridboxes
        for xi in range(0, df.shape[0] - 1):
            for yi in range(0, df.shape[1] - 1):
                colind = gridbox_cind[xi, yi] - 1

                geoJSON[colind]["features"].append(
                    {
                        "type": "Feature",
                        "properties": {},
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [
                                    [x[xi, yi], y[xi, yi]],
                                    [x[xi + 1, yi], y[xi + 1, yi]],
                                    [x[xi + 1, yi + 1], y[xi + 1, yi + 1]],
                                    [x[xi, yi + 1], y[xi, yi + 1]],
                                    [x[xi, yi], y[xi, yi]],
                                ]
                            ],
                        },
                    }
                )

        # loop over # of colors and create a new layer for each
        for i in range(len(colors)):
            geoLayer = dict(
                sourcetype="geojson",
                source=geoJSON[i],
                type="fill",
                color=mplcol.rgb2hex(colors[i]),
                opacity=0.4,
                name="{} mph".format(colors[i]),
            )
            geo_layout["mapbox"]["layers"].append(geoLayer)

        if points:
            poly_box = {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {},
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [
                                    [
                                        points["range"]["mapbox"][0][0],
                                        points["range"]["mapbox"][1][1],
                                    ],
                                    [
                                        points["range"]["mapbox"][0][0],
                                        points["range"]["mapbox"][0][1],
                                    ],
                                    [
                                        points["range"]["mapbox"][1][0],
                                        points["range"]["mapbox"][0][1],
                                    ],
                                    [
                                        points["range"]["mapbox"][1][0],
                                        points["range"]["mapbox"][1][1],
                                    ],
                                    [
                                        points["range"]["mapbox"][0][0],
                                        points["range"]["mapbox"][1][1],
                                    ],
                                ]
                            ],
                        },
                    }
                ],
            }
            geo_layout["mapbox"]["layers"].append(
                dict(
                    sourcetype="geojson",
                    source=poly_box,
                    type="line",
                    opacity=1.0,
                    line=dict(width=3, color="#ffffff", dash="dash"),
                    layer="above",
                )
            )

        return dict(data=data, layout=geo_layout)
    else:
        return dict(data=[], layout=geo_layout)


# definte utility functions, could be placed in another script
def transform_from_latlon(lat, lon):
    lat = np.asarray(lat)
    lon = np.asarray(lon)
    trans = Affine.translation(lon[0], lat[0])
    scale = Affine.scale(lon[1] - lon[0], lat[1] - lat[0])
    return trans * scale


def rasterize(poly, lat_coord, long_coord, fill=np.nan, **kwargs):
    """Rasterize a list of (geometry, fill_value) tuples onto the given
    xray coordinates. This only works for 1d latitude and longitude
    arrays.
    """
    transform = transform_from_latlon(lat_coord, long_coord)
    out_shape = (len(lat_coord), len(long_coord))
    raster = features.rasterize(
        poly,
        out_shape=out_shape,
        fill=np.nan,
        transform=transform,
        dtype=float,
        **kwargs
    )
    return xr.DataArray(
        raster, coords=(lat_coord, long_coord), dims=("south_north", "west_east")
    )

if __name__ == '__main__':
    app.run_server(debug=True,port=3000,host='0.0.0.0')
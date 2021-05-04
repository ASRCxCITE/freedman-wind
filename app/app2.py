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
                        dcc.Loading(id="main-header-loading",
                                    children=[html.H3(id="main-header",children=[])],
#                                     fullscreen=True
                                   )
#                         html.H3("Forecast as of "+str(dt.datetime.today().strftime("%b %d, %Y %H:%M"))),
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
                                    id="selected-hours",
                                    options=[{'label':'All (120)','value':0},
                                             {'label':'Every 3','value':1},
                                             {'label':'Every 6','value':2},
                                             {'label':'Every 12','value':3},
#                                              {'label':'Custom','value':4},
                                            ],
                                    value=2,
                                    labelStyle={'display': 'inline-block', 'paddingRight':'10px'}),
                                dbc.Button("Fetch Data", id="hour-button", size='sm'),
                            ],style={'marginLeft':5,'marginRight':5},justify='start'),    
                            dbc.Row([
                                html.Div([
                                    dcc.Checklist(
                                        id="custom-hours",
                                        options=[{'label':k+1,'value':k+1} for k in range(120)],
                                        value=[1,10],
                                        labelStyle={"vertical-align":"middle"},
                                        style={"display":"inline-flex", 
                                               "flex-wrap":"wrap", 
                                               "justify-content":"space-between"}
                                    ),
                                ],id="custom-hours-div",
                                    style={})
                            ],style={},justify='center'),  
                        ],style={},align='left'),
                    ],style={'width':'100%'},
                ),
                # dbc.Progress(id="progress",value="0",animated=True),
                dcc.Loading(
                    id="data-loading",
                    children=[dcc.Store(id="geojson-data")],
#                     children=[dcc.Store(id="wind-data"),dcc.Store(id="geojson-data"),dcc.Store(id="geojson-annot")],
#                     fullscreen=True,
                ),
#                 dcc.Loading(
#                     id="wind-data-loading",
# #                     children=[dcc.Store(id="geojson-data"),dcc.Store(id="geojson-annot")],
#                     children=[dcc.Store(id="wind-data")],
# #                     fullscreen=True,
#                 ),
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
                                max=13,
                                step=None,
                                allowCross=False,
                                value=[0, 6],
                                pushable=4,
                                updatemode="mouseup",
                            ),
                            width=9,
                            
                        ),
#                         dbc.Col(dbc.Button("Update Plot!", id="button")),
                    ],
                    className="d-flex justify-content-center pt-4 w-100",
                ),
                dbc.Row(
                    [
                        dbc.Col(
#                             dcc.Loading(
#                                 id="loading-animation",
#                                 children=[
                            [
#                                     dcc.Store(id="geojson-data"),
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
                                    ),
                                    dbc.Row([
                                        dbc.Button(" << ", id="button-prev", n_clicks=0),
                                        dcc.Loading(id="map-time-loading",children=[html.H5(id="map-time",children=[])]),
                                        dbc.Button(" >> ", id="button-next", n_clicks=0),
                                    ],align='center',justify='center')
                                    
                                ],
#                             )
                            
                        ),
                        dbc.Col(
                            dcc.Loading(
                                id="loading-line",
                                children=[
                                    dcc.Store(id="geojson-annot"),
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
    [
#         Output("wind-data", "data"), Output("fdate", "marks"), 
        Output("main-header","children"), Output("geojson-data","data"), Output("geojson-annot","data"),
        Output("fdate", "marks"),Output("fdate", "max")
    ],[
        Input("hour-button","n_clicks")
    ],[
        State("selected-hours","value"),#State("wind-data", "data"),
        State("geojson-data","data"),State("geojson-annot","data")
    ],
)
def load_data(click, hours, geojson, annot):
# def load_data(click, hours, data, geojson, annot):

    print("Loading Data",click,hours)
    hour_button_click = click
    
    print('request geo from app')
    response = requests.get("http://169.226.181.187:7006?hour="+str(hours))
    res = response.json()
    print('geo request complete')
    
    print('keys',res['geojson']['geojson'].keys()) 
    return(
        html.H3("Forecast as of "+str(pd.to_datetime(res['geojson']['time'],unit='s').strftime("%b %d, %Y %H:%M"))),
        res['geojson']['geojson'],#[list(res['geojson']['geojson'].keys())[0]],
        res['geojson']['data'],#[list(res['geojson']['data'].keys())[0]],
        res['geojson']['marks'],
        int(list(res['geojson']['marks'].keys())[-1])
        
    )
    

# @app.callback(
#     [
#         Output("wind-data", "data")#, Output("fdate", "marks"), 
# #         Output("main-header","children"), Output("geojson-data","data"), Output("geojson-annot","data")
#     ],[
#         Input("hour-button", "n_clicks")
#     ],[
#         State("selected-hours","value"), State("wind-data","data")
# #         State("geojson-data","data"),State("geojson-annot","data")
#     ],
# )
# def load_gust_data(click, hours, data):

#     print('request gust from app')
#     response = requests.get("http://169.226.181.187:7006/gust?hour="+str(hours))
#     res = response.json()
# #     data = res['gust']
#     print('gust request complete')
#     return(
#         [res['gust']]
#     )
    
@app.callback(
    [
        Output('custom-hours', 'labelStyle'),
        Output('custom-hours-div','style')
    ],
    Input('selected-hours', 'value')
)
def forecast_hours(value):
    if value == 4:
        return [{"display":"inline-block", "flex-wrap":"wrap", "justify-content":"space-between"},
                {'marginLeft':5,'width':'50%','padding':5,'max-height':'100px',
                 'overflow':'scroll',"border":"1px white solid"}]
    else: return [{"display":"none"},
                  {"border":"0px white solid"}]

@app.callback(
    Output("line-plot", "figure"),
    [
#         Input("wind-data", "data"),
        Input("geojson-annot","data"),
        Input("geoanimation", "selectedData"),
        Input("hour-button", "n_clicks"),
        Input("fdate", "value"),
#         Input('selected-hours','value')
    ],
    [State('selected-hours','value')],
)
def plot_line(annot, points, hours, dateind, selectedHours):
    
    print('plot line start',dateind,selectedHours)
    
    step = 6
    if selectedHours == 0: step = 1
    elif selectedHours == 1: step = 3
    elif selectedHours == 2: step = 6   
    elif selectedHours == 3: step = 12
    
        
    if points and annot and dateind:
        print('plot line',dateind[-1]/step,int(dateind[0]/step), 
              int(dateind[-1]/step)+1,points["range"]["mapbox"][1][1], 
              points["range"]["mapbox"][0][1],points["range"]["mapbox"][0][0], 
              points["range"]["mapbox"][1][0])

        keys = [list(annot.keys())[i] for i in range(int(dateind[0]/step), int(dateind[-1]/step)+1)]
        max_wind = []
        for k in keys:
            valid_lat = [i for i,l in enumerate(annot[k][0]['lat']) 
                         if (l>=points["range"]["mapbox"][1][1])and(l<=points["range"]["mapbox"][0][1])]
            valid_lon = [i for i,l in enumerate(annot[k][0]['lon']) 
                         if (l>=points["range"]["mapbox"][0][0])and(l<=points["range"]["mapbox"][1][0])]
            lat_lon_intersect = np.intersect1d(valid_lat,valid_lon)
            max_wind.append(max([annot[k][0]['values'][i] for i in lat_lon_intersect]))

        data = dict(
            type="scatter",
            x=keys,
            y=max_wind,
#             x=df.Time.values,#pd.to_datetime(df.Time.values).strftime("%m/%d %H:%M"),
#             y=df.values,
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
    [Output("geoanimation", "figure"),Output('button-next','n_clicks'),Output('map-time','children')],
    [
        Input("geojson-data", "data"),
        Input("geojson-annot","data"),
        Input("button-next", "n_clicks"),
        Input("button-prev", "n_clicks"),
        Input("hour-button", "n_clicks"),
        Input("fdate", "value"),
    ],
    [State("geoanimation", "selectedData"),State('selected-hours','value')],
)
# def plot_geo_animation(geo_layout, annot, data, n, dateind, points):
def plot_geo_animation(geo, annot1, forwardClicks, backClicks, hourClicks, dateind, points, selectedHours):
    
    step = 6
    if selectedHours == 0: step = 1
    elif selectedHours == 1: step = 3
    elif selectedHours == 2: step = 6   
    elif selectedHours == 3: step = 12
        
    print('before click',forwardClicks,dateind[-1]/step,len(dateind)-1)
    
    if(forwardClicks > dateind[-1]/step): forwardClicks = 0
    forwardClicks = int(min(forwardClicks,dateind[-1]/step))
    index = list(geo.keys())[forwardClicks]

    print('clicks', forwardClicks, index)
    
    geo_layout = geo[index]
    annot = annot1[index]
    
#     print(geo_layout[index])
    
    if annot and dateind:

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
            

        return [dict(data=annot, layout=geo_layout),forwardClicks,index]
    else:
        return [dict(data=[], layout=geo_layout),forwardClicks,index]


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
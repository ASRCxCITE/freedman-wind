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


#-- Configuration Variables --#
mapbox_token='pk.eyJ1IjoibnNjaGlyYWxkaSIsImEiOiJjanoxOXlraTMwY3RyM2hzMDdhM2RxZGk2In0.3SgrGa7NM-r-MFVHl1lDmw'
counties={
    '119': 'Westchester',
    '081': 'Queens',
    #'061': 'Manhattan',
    '085': 'Staten Island',
    '005': 'Bronx',
    '047': 'Brooklyn'
}

#-- global variables --#
shp=shpreader.Reader('/network/rit/lab/schiraldilab/shapefiles/us_county/tl_2018_us_county')
polys={}
for r in shp.records():
    if r.attributes['STATEFP'] =='36' and r.attributes['COUNTYFP'] in counties.keys():
        polys[counties[r.attributes['COUNTYFP']]]=r.geometry

# power_lines=requests.get('https://opendata.arcgis.com/datasets/70512b03fe994c6393107cc9946e5c22_0.geojson')
# power_lines=power_lines.json()

#-- Specify layout components --#
body=dbc.Container([
    dbc.Container([
        dbc.Row([
            html.H2("Initialization Date:"),
            dcc.DatePickerSingle(
                id='selected-date',
                min_date_allowed=dt.datetime(2017, 10, 29),
                max_date_allowed=dt.datetime(2017, 10, 29),
                initial_visible_month=dt.datetime(2017, 10, 29),
                date=str(dt.datetime(2017, 10, 29)),
                className='pl-3'
            ),
        ],className='p-2'),
        #dbc.Progress(id="progress",value="0",animated=True),
        dcc.Loading(
            id='data-loading',
            children=[dcc.Store(id='wind-data')],
            fullscreen=True
        ),
        dbc.Row([
            dbc.Col(
                dcc.Markdown(
                '''
                County polygon colors indicate the risk across the full forecast window. Risk thresholds are defind by the percent of grid points in a county exceeding a given threshold.
                - Green:  100% of county < 30 mph for **all** 6 hour windows
                - Yellow: > 1% of county between 30mph and 50mph for **any** 6 hour window
                - Red:    > 1% of county exceeding 50mph for **any** 6 hour window
                '''
                )
            ),dbc.Col(
                html.P(
                """Line charts detail the rolling mean 6 hour risk score. X-Axis dates indicate the end of the 6 hour window.
                Click on any county polygon to display the forecast risk.
                """
                )
            ),
        ],className='d-flex justify-content-center pt-1 w-100'),
        dbc.Row([
            dbc.Col(
                dcc.Loading(id='loading-map',children=[
                    dcc.Graph(
                        id='geomap',
                        figure=dict(
                            layout=dict(
                                mapbox=dict(
                                    accesstoken=mapbox_token,
                                    center=dict(
                                        lon=-73.842474,
                                        lat=40.861137
                                    ),
                                    zoom=7,
                                    style='dark'
                                ),
                                paper_bgcolor="#303030",
                                margin = dict(l = 0, r = 0, t = 0, b = 0) 
                            )
                        )
                    ),
                ]),
            ),
            dbc.Col(
                dcc.Loading(id='loading-line',children=[
                    dcc.Graph(id='line-plot',figure=dict(
                            layout=dict(
                                title='Click on a Polygon',
                                paper_bgcolor="#303030", 
                                plot_bgcolor="#4a4a4a",
                                font=dict(
                                    color='white'
                                ),
                                # margin=dict(t=30,b=40,l=20,r=20)
                            )
                        )
                    )
                ])
            ),
        ],className='d-flex justify-content-center pt-1 w-100'),
        html.Hr(),
        # dbc.Row([
        #     dcc.Loading(id='loading-animation',children=[
        #         html.Div(id='date-slider'),
        #         dcc.Graph(
        #             id='geoanimation',
        #             figure=dict(
        #                 layout=dict(
        #                     mapbox=dict(
        #                         accesstoken=mapbox_token,
        #                         center=dict(
        #                             lon=-73.842474,
        #                             lat=40.861137
        #                         ),
        #                         zoom=7,
        #                         style='dark'
        #                     ),
        #                     paper_bgcolor="#303030",
        #                     margin = dict(l = 0, r = 0, t = 0, b = 0) 
        #                 )
        #             )
        #         ),
                
        #     ]),
        # ],className='d-flex justify-content-center p-1 w-100'),
    ]),
],fluid=True)

#-- Initialize the flask application --#
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY,dbc.themes.GRID])
app.layout=html.Div([body])
app.title="ConEd WindView"
server=app.server

# Define callback functions
@app.callback(
    Output('wind-data','data'),
    [Input('selected-date','date')],
    [State('wind-data','data')]
)
def load_data(date,data):

    print('Loading Data for {0}'.format(str(date)))
    flist = glob.glob('./netcdf/wrfout_d01*')
    U10=[]
    V10=[]
    for f in sorted(flist):
        df = nc.Dataset(f)
        U10.append(wrf.getvar(df,'U10'))
        V10.append(wrf.getvar(df,'V10'))

    V10=xr.concat(V10,'Time')
    U10=xr.concat(U10,'Time')
    mag= np.sqrt(U10**2+V10**2) * 2.23694
    mag.name='speed'

    # Modify for plotting
    mag['south_north']=mag.XLAT.values[:,0]
    mag['west_east']=mag.XLONG.values[0,:]
    print('data loaded')

    slider=dcc.RangeSlider(
        id='fdate',
        min=0,
        max=len(mag.Time),
        step=1,
        allowCross=False,
        marks={k: pd.to_datetime(mag.Time.values[k]).strftime('%m/%d %H:%M') for k in range(len(mag.Time))}
    )
    return mag.to_dict()


@app.callback(    
    Output('geomap','figure'),
    [
        Input('selected-date','date'),
        Input('wind-data','data'),
    ]
)
def plot_geo(date,data):

    # data to xarray
    data=xr.DataArray.from_dict(data)

    # figure for curves
    fig = make_subplots(rows=1, cols=3,
                          shared_xaxes=True, shared_yaxes=True,
                          vertical_spacing=0.001)

    counter=0
    shapes=[]
    curves={}
    for k,v in polys.items():
        # Create rasters of each county shape so that we can assess the risk within the boundaries
        r = rasterize([v],data.coords['south_north'],data.coords['west_east'])
        masked=(data*r).rolling(Time=6).mean().isel(Time=slice(5,None))

        # categorize by % of grid coverage
        if np.all(((masked<30).sum(['south_north','west_east']) / r.sum()) == 1):
            shapes.append(
                 go.Scattermapbox(
                    lon=v.boundary.xy[0].tolist(),
                    lat=v.boundary.xy[1].tolist(),
                    mode='lines',
                    line=dict(
                        color='black',
                        width=2
                    ),
                    fill='toself',
                    fillcolor='rgba(0,128,0,0.65)',
                    text=k,
                    name=k,
                    showlegend=False,
                 )
            )
        elif np.any(masked>=50):
            shapes.append(
                 go.Scattermapbox(
                    lon=v.boundary.xy[0].tolist(),
                    lat=v.boundary.xy[1].tolist(),
                    mode='lines',
                    line=dict(
                        color='black',
                        width=2
                    ),
                    fill='toself',
                    fillcolor='rgba(255,0,0,0.65)',
                    text=k,
                    name=k,
                    showlegend=False,
                 )
            )
        else:
            shapes.append(
                 go.Scattermapbox(
                    lon=v.boundary.xy[0].tolist(),
                    lat=v.boundary.xy[1].tolist(),
                    mode='lines',
                    line=dict(
                        color='black',
                        width=2
                    ),
                    fill='toself',
                    fillcolor='rgba(255,165,0,0.65)',
                    text=k,
                    name=k,
                    showlegend=False,
                 )
            )

    geo_layout=dict(
        #hovermode='closest',
        mapbox=dict(
            accesstoken=mapbox_token,
            center=dict(
                lon=-73.842474,
                lat=40.861137
            ),
            zoom=7,
            style='dark',
            # layers=[dict(
            #     sourcetype='geojson',
            #     source=power_lines,
            #     type='lines',
            #     color='blue',
            #     line=dict(
            #         width=1
            #     )
            # )]
        ),
        paper_bgcolor="#303030",
        margin = dict(l = 0, r = 0, t = 0, b = 0)
    )
    
    geo_plots={
        "data": shapes,
        "layout": geo_layout
    }

    return geo_plots#, curves['Staten Island']

@app.callback(
    Output('line-plot','figure'),
    [
        Input('wind-data','data'),
        Input('geomap','clickData')
    ]
)
def plot_line(data,point):

    if point:
        clicked=list(polys.keys())[point['points'][0]['curveNumber']]
    else:
        clicked='Westchester'

    if data:
        # data to xarray
        data=xr.DataArray.from_dict(data)

        r = rasterize([polys[clicked]],data.coords['south_north'],data.coords['west_east'])
        masked=(data*r).rolling(Time=6).mean().isel(Time=slice(5,None))

        plot=dict(
            data=[
                go.Scatter(
                    y=((masked<30).sum(['south_north','west_east']) / r.sum())*100,
                    x=pd.to_datetime(masked.Time.values).strftime("%m/%d %H:%M"),
                    name='Low Wind',
                    line=dict(
                        color='green'
                    ),
                    showlegend=False,
                    hovertext=[
                        "{0}: {1}-{2}<br>{3}: {4:.2f}%".format(
                            'Valid Period',
                            (pd.to_datetime(d.Time.values)-pd.Timedelta(hours=5)).strftime('%m/%d %H:%M'),
                            pd.to_datetime(d.Time.values).strftime('%m/%d %H:%M'),
                            'Grid Coverage',
                            d.values
                        ) for d in (((masked<30).sum(['south_north','west_east']) / r.sum())*100).fillna(0)
                    ],
                    hoverinfo="text",
                ),
                go.Scatter(
                    y=(((masked>=30) & (masked<=50)).sum(['south_north','west_east']) / r.sum())*100,
                    x=pd.to_datetime(masked.Time.values).strftime("%m/%d %H:%M"),
                    name='Moderate Wind',
                    line=dict(
                        color='yellow'
                    ),
                    showlegend=False,
                    hovertext=[
                        "{0}: {1}-{2}<br>{3}: {4:.2f}%".format(
                            'Valid Period',
                            (pd.to_datetime(d.Time.values)-pd.Timedelta(hours=5)).strftime('%m/%d %H:%M'),
                            pd.to_datetime(d.Time.values).strftime('%m/%d %H:%M'),
                            'Grid Coverage',
                            d.values
                        ) for d in ((((masked>=30) & (masked<=50)).sum(['south_north','west_east']) / r.sum())*100).fillna(0)
                    ],
                    hoverinfo="text",
                ),
                go.Scatter(
                    y=((masked>50).sum(['south_north','west_east']) / r.sum())*100,
                    x=pd.to_datetime(masked.Time.values).strftime("%m/%d %H:%M"),
                    name='High Wind',
                    line=dict(
                        color='red'
                    ),
                    showlegend=False,
                    hovertext=[
                        "{0}: {1}-{2}<br>{3}: {4:.2f}%".format(
                            'Valid Period',
                            (pd.to_datetime(d.Time.values)-pd.Timedelta(hours=5)).strftime('%m/%d %H:%M'),
                            pd.to_datetime(d.Time.values).strftime('%m/%d %H:%M'),
                            'Grid Coverage',
                            d.values
                        ) for d in (((masked>50).sum(['south_north','west_east']) / r.sum())*100).fillna(0)
                    ],
                    hoverinfo="text",
                )
            ],
            layout=dict(
                hovermode='closest',
                title='WindRisk {0}'.format(clicked),
                yaxis=dict(
                    title='% Coverage',
                    nticks=10,
                    gridcolor="#d3d3d3"
                ),
                xaxis=dict(
                    title="6-h Period Ending",
                    nticks=10,
                    gridcolor='#d3d3d3'
                ),
                paper_bgcolor="#303030", 
                plot_bgcolor="#4a4a4a",
                font=dict(
                    color='white'
                ),
            )
        )

        return plot

# @app.callback(    
#     Output('geoanimation','figure'),
#     [
#         Input('selected-date','date'),
#         Input('wind-data','data'),
#         Input('fdate','value'),
#     ]
# )
# def plot_geo_animation(date,data,selected_dates):

#     # data to xarray
#     data=xr.DataArray.from_dict(data)
#     df=data.isel(Time=selected_dates).max('Time')

#     # Set up Colors
#     bins=np.arange(5,51,5)
#     norm=mplcol.Normalize(bins[0],bins[-1])
#     colors=cm.viridis(norm(bins))

#     annotations = [dict(
#         showarrow = False,
#         #align = 'right',
#         text = '<b>MPH</b>',
#         bgcolor = '#EFEFEE',
#         x = 0.90,
#         y = 0.915,
#     )]

#     for i in range(0,len(colors)-1):
#         #color = cm[bin]
#         annotations.append(
#             dict(
#                 arrowcolor = mplcol.rgb2hex(colors[i]),
#                 text = ('{:01.1f}').format(bins[i]),
#                 height = 21,
#                 x = 0.95,
#                 y = 0.85-(i/20),
#                 ax = -55,
#                 ay = 0,
#                 arrowwidth = 23,
#                 arrowhead = 0,
#                 bgcolor = '#EFEFEE'
#             )
#         )

#     geo_layout=dict(
#         mapbox=dict(
#             accesstoken=mapbox_token,
#             center=dict(
#                 lon=-73.842474,
#                 lat=40.861137
#             ),
#             zoom=6,
#             style='dark',
#             layers=[]
#         ),
#         plot_bgcolor="#303030",
#         paper_bgcolor="#303030",
#         margin = dict(l = 0, r = 0, t = 0, b = 0),
#         annotations=annotations
#     )

        
#     # Get the max
#     x,y=np.meshgrid(df.west_east.values,df.south_north.values) 

#     data=[dict(
#         type='scattermapbox',
#         lon=x.flatten()[::2],
#         lat=y.flatten()[::2],
#         text=['{0:.1f} mph'.format(i) for i in df.values.flatten()[::2]],
#         hoverinfo='text',
#         mode='none',
#     )]
#     gridbox_cind=np.digitize(df.values,bins)

#     # set up geosjon
#     geoJSON=[{
#             'type': 'FeatureCollection',
#             'features': []
#             } for i in range(len(colors))]

#     # each "color" is its own geojson layer for plotly. Loop of lat/lon and create gridboxes
#     for xi in range(0,df.shape[0]-2,2):
#         for yi in range(0,df.shape[1]-2,2):
#             colind=gridbox_cind[xi,yi]-1
            
#             geoJSON[colind]['features'].append({
#                 'type': 'Feature',
#                 'properties':{},
#                 'geometry': {
#                     'type': 'Polygon',
#                     'coordinates': [[
#                         [x[xi,yi],y[xi,yi]],
#                         [x[xi+2,yi],y[xi+2,yi]],
#                         [x[xi+2,yi+2],y[xi+2,yi+2]],
#                         [x[xi,yi+2],y[xi,yi+2]],
#                         [x[xi,yi],y[xi,yi]]
#                     ]]
#                 }
#             })
            
#     # loop over # of colors and create a new layer for each
#     for i in range(len(colors)):
#         geoLayer=dict(
#             sourcetype='geojson',
#             source=geoJSON[i],
#             type='fill',
#             color=mplcol.rgb2hex(colors[i]),
#             opacity=0.5
#         )
#         geo_layout['mapbox']['layers'].append(geoLayer)
#     return dict(data=data,layout=geo_layout)

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
    transform = transform_from_latlon(lat_coord,long_coord)
    out_shape = (len(lat_coord), len(long_coord))
    raster = features.rasterize(poly, out_shape=out_shape,
                                fill=np.nan, transform=transform,
                                dtype=float,**kwargs)
    return xr.DataArray(raster, coords=(lat_coord,long_coord), dims=('south_north', 'west_east'))

if __name__=='__main__':
    app.run_server()
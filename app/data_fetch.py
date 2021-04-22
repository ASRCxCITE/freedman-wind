from ftplib import FTP
import os
import json
import glob
import xarray as xr
import netCDF4 as nc
import pandas as pd
import numpy as np
from datetime import datetime
import threading
import pickle as pkl

ftp_host = 'ftp.gridpointweather.com'
ftp_acct = 'wefs'
ftp_pass = 'conED#18'

mtimes = {}

def setInterval(func,time):
    e = threading.Event()
    while not e.wait(time):
        func()


def grabFile(filename,ftp,directory):
    with open(directory+'/'+filename, 'wb') as localfile:
        ftp.retrbinary('RETR ' + filename, localfile.write, 1024)
#     localfile.close()
    
def ftp_fetch():
    print('fetching...',datetime.now())
    files = []
    count = 0
    with FTP(ftp_host) as ftp:
        ftp.login(ftp_acct, ftp_pass) # connect to host, default port
        dirs = ftp.nlst()
        ftp.cwd(dirs[0])
        for d in dirs:
            directory = 'netcdf/'+d
            if not os.path.exists(directory):os.makedirs(directory)
            ftp.cwd('../'+d)

            ls = []
            ftp.retrlines('LIST', ls.append)
            for entry in ls:
                m = int(datetime.strptime(entry.split()[5],'%b').strftime('%m'))
                d = int(entry.split()[6])
                h = int(entry.split()[7].split(':')[0])
                mi = int(entry.split()[7].split(':')[1])
                dt = datetime(datetime.now().year, m, d, h, mi)
                
                if entry.split()[-1] not in mtimes: mtimes[entry.split()[-1]] = {'time':dt,'update':True}
                else:
                    if dt!=mtimes[entry.split()[-1]]['time']:mtimes[entry.split()[-1]] = {'time':dt,'update':True}
                    else:mtimes[entry.split()[-1]] = {'time':dt,'update':False}
                        
#                 print(entry.split()[-1],dt,mtimes[entry.split()[-1]]['time'])
            files=ftp.nlst()
            
            for f in files: 
                if mtimes[f]['update']:
                    count = count + 1
                    grabFile(f,ftp,directory)
        print(str(count)+' files have been updated')
        ftp.quit()
#     if count>0: save_data_as_obj()
    return count
        
        
def get_geoJson(gust_sel):
    import matplotlib.colors as mplcol
    import numpy as np
    from matplotlib import cm

    # Set up Colors
    bins = np.arange(0, 61, 5)
    norm = mplcol.Normalize(bins[0], bins[-1])
    colors = cm.viridis(norm(bins))

    mapbox_token = "pk.eyJ1IjoibnNjaGlyYWxkaSIsImEiOiJjanoxOXlraTMwY3RyM2hzMDdhM2RxZGk2In0.3SgrGa7NM-r-MFVHl1lDmw"
    ZOOM=7
    CENTER_LAT=41.019801
    CENTER_LONG=-73.723068




    df = (xr.DataArray.from_dict(gust_sel)
#           .max("Time")
          .coarsen(south_north=6, west_east=6, boundary="pad")
          .max()
         )

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
    geo_layout = {}
    data = {}
    for i,tv in enumerate(df.Time.values):
        
        geo_layout[tv] = dict(
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
        data[tv] = {}
    for i,tv in enumerate(df.Time.values):

        geo_layout[tv]["annotations"] = annotations

        # Get the max
        x, y = np.meshgrid(df[i].west_east.values, df[i].south_north.values)
        gridbox_cind = np.digitize(df[i].values, bins)

        data[tv] = [
            dict(
                type="scattermapbox",
                lon=x.flatten().tolist(),
                lat=y.flatten().tolist(),
                text=["{0:.1f} mph".format(i) for i in df[i].values.flatten()],
                hoverinfo="text",
                mode="none",
            )
        ]

        # set up geosjon
        geoJSON = [
            {"type": "FeatureCollection", "features": []} for i in range(len(colors))
        ]

        # each "color" is its own geojson layer for plotly. Loop of lat/lon and create gridboxes
        for xi in range(0, df[i].shape[0] - 1):
            for yi in range(0, df[i].shape[1] - 1):
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

        for i in range(len(colors)):
            geoLayer = dict(
                sourcetype="geojson",
                source=geoJSON[i],
                type="fill",
                color=mplcol.rgb2hex(colors[i]),
                opacity=0.4,
                name="{} mph".format(colors[i]),
            )
            geo_layout[tv]["mapbox"]["layers"].append(geoLayer)
        
    return [geo_layout, data]
        
        
def save_data_as_obj():
    print('save data as obj...')
    flist = sorted(glob.glob('netcdf/gust/WEFS_max_gust*'))
    gust = []
    all_times = []
    for f in flist:
        df = nc.Dataset(f)
    #     max_gust = wrf.getvar(df,'max_gust',meta=False)
    #     max_gust.append(df.variables['max_gust'][:].data)
        max_gust = df.variables['max_gust'][:].data
        latitude = df.variables['latitude'][:].data
        longitude = df.variables['longitude'][:].data
        all_times.append(df.variables['time'][:].data[0])

        gust.append(xr.DataArray(
            data = max_gust,
            dims = ["south_north","west_east"],
            coords=dict(
                south_north = (["south_north"],latitude),
                west_east = (["west_east"],longitude)
            ),
            attrs=dict(
                units= df.variables['max_gust'].units,
                level= df.variables['max_gust'].level,
                long_name= df.variables['max_gust'].long_name,
                short_name= df.variables['max_gust'].short_name,
                time= df.variables['max_gust'].time,
                nlat= df.variables['max_gust'].nlat,
                nlon= df.variables['max_gust'].nlon,
                description= df.variables['max_gust'].description,
#                 _FillValue= df.variables['max_gust']._FillValue

            ))

        )


    gust=xr.concat(gust,'Time')
    gust['Time'] = [pd.to_datetime(all_times[k],unit='s').strftime("%m/%d %H:%M")
                    for k in range(len(gust.Time))]


    print("data loaded")

    marks = {
        k: pd.to_datetime(all_times[k],unit='s').strftime("%m/%d %H:%M")
        for k in range(0, len(gust.Time))
    }
#     print(gust)
    gust_sel = gust.sel(south_north=slice(40.06, 42.47), west_east=slice(-75.2, -71.84)).to_dict()
    geojson = get_geoJson(gust_sel)
    
    print('saving data...')


    with open('json/gust.json','w') as json_file:
        json.dump({'gust':gust_sel},json_file)
    with open('json/gust_geojson.json','w') as geojson_file:
        json.dump({'geojson':geojson[0],'data':geojson[1],'time':gust[0].time,'marks':marks},geojson_file)
#         pkl.dump({'geojson':geojson[0],'data':geojson[1],'time':min(all_times)-3600,'marks':marks},geojson_file)
    
    print('complete')
    
def execute():
    count = ftp_fetch()
#     count = 1
    if count>0: save_data_as_obj()

if __name__ == '__main__':
    execute()
    setInterval(execute,60*30)
#     print('test')
    

    # print(files)
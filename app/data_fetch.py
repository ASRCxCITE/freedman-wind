from ftplib import FTP
import os
import json
import glob
import xarray as xr
import netCDF4 as nc
import pandas as pd

ftp_host = 'ftp.gridpointweather.com'
ftp_acct = 'wefs'
ftp_pass = 'conED#18'


def grabFile(filename,ftp,directory):
    localfile = open(directory+'/'+filename, 'wb')
    ftp.retrbinary('RETR ' + filename, localfile.write, 1024)
    localfile.close()
    
def ftp_fetch():
    files = []
    with FTP(ftp_host) as ftp:
        ftp.login(ftp_acct, ftp_pass) # connect to host, default port
        dirs = ftp.nlst()
        ftp.cwd(dirs[0])
        for d in dirs:
            directory = 'netcdf/'+d
            if not os.path.exists(directory):os.makedirs(directory)
            ftp.cwd('../'+d)
        #     ls = []
        #     ftp.retrlines('LIST', ls.append)
        #     for entry in ls:
        #         print('e',entry)
            files=ftp.nlst()
            for f in files: grabFile(f,ftp,directory)
        ftp.quit()
        
        
        
def save_data_as_obj():

    flist = glob.glob('netcdf/gust/WEFS_max_gust*')
    gust = []
    for f in flist[0:2]:
        df = nc.Dataset(f)
    #     max_gust = wrf.getvar(df,'max_gust',meta=False)
    #     max_gust.append(df.variables['max_gust'][:].data)
        max_gust = df.variables['max_gust'][:].data
        latitude = df.variables['latitude'][:].data
        longitude = df.variables['longitude'][:].data

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
                _FillValue= df.variables['max_gust']._FillValue

            ))

        )


    gust=xr.concat(gust,'Time')
    gust['Time'] = [pd.to_datetime(gust[k].time+3600*(k+1),unit='s').strftime("%m/%d %H:%M")
                    for k in range(len(gust.Time))]


    print("data loaded")

    marks = {
        k: pd.to_datetime(gust[k].time+3600*(k+1),unit='s').strftime("%m/%d %H:%M")
        for k in range(0, len(gust.Time), 8)
    }
#     print(gust)

    with open('json/gust.json','w') as json_file:
        json.dump({'gust':gust.sel(
                south_north=slice(40.06, 42.47), west_east=slice(-75.2, -71.84)
            ).to_dict(),'marks':marks,'time':gust[0].time},
                  json_file)
    

#     return (
#         gust.sel(
#             south_north=slice(40.06, 42.47), west_east=slice(-75.2, -71.84)
#         ).to_dict(),
#         marks
#     )

if __name__ == '__main__':
    ftp_fetch()
    save_data_as_obj()

    # print(files)
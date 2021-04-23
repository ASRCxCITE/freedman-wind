# freedman-wind
Author: K. Sulia, xCITE Lab

Front-end displays maximum wind gust in domain. Selected area results in maximum wind speed inside the box as a time series.

Scripts:
1. app2.py -- this is the primary front-end code
2. api.py -- this is the backend API from which data is fetched. Attempts here to limit computations inside this script to reduce fetch time lag, except minor data manipulation via fetch queries (specific hours, resolution).
3. api_ping.py -- this will be a consistently running python script that periodically (every 30 minutes), pings the api.py script and executes the ping_geo() and ping_gust() functions. This loads pre-generated (on file) JSON files into the API (into global variables) so that these data are already available when the front-end makes an API request. This reduces lag even further, limiting real-time IO bottlenecks on fetch.
4. data_fetch.py -- this is a background task that periodically (every 30 min) fetches the latest WEFS data from the provided FTP. Upon receiving this data, a number of tasks are completed to manipulate the data into formats amenable for front-end display (as originally coded by N. Shiraldi in app2.py!). As of Apr 22, 2021, the two JSON files that are saved are 'gust.json' and 'geojson_data.json', and serve as the data sources for the map display and timeseries graphs, respectively.  


All of the above scripts will need to be run as consistent background tasks. Perhaps there is a better way to do this (consolidate!), but it is what it is for now!

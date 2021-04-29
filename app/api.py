import flask
from flask import request, jsonify
import os
import json
import pickle as pkl
from datetime import datetime
import copy

app = flask.Flask(__name__)
app.config["DEBUG"] = True

# # Create some test data for our catalog in the form of a list of dictionaries.
# books = [
#     {'id': 0,
#      'title': 'A Fire Upon the Deep',
#      'author': 'Vernor Vinge',
#      'first_sentence': 'The coldsleep itself was dreamless.',
#      'year_published': '1992'},
#     {'id': 1,
#      'title': 'The Ones Who Walk Away From Omelas',
#      'author': 'Ursula K. Le Guin',
#      'first_sentence': 'With a clamor of bells that set the swallows soaring, the Festival of Summer came to the city Omelas, bright-towered by the sea.',
#      'published': '1973'},
#     {'id': 2,
#      'title': 'Dhalgren',
#      'author': 'Samuel R. Delany',
#      'first_sentence': 'to wound the autumnal city.',
#      'published': '1975'}
# ]


# @app.route('/', methods=['GET'])
# def home():
#     return '''<h1>Distant Reading Archive</h1>
# <p>A prototype API for distant reading of science fiction novels.</p>'''


# @app.route('/api/v1/resources/books/all', methods=['GET'])
# def api_all():
#     return jsonify(books)


# @app.route('/api/v1/resources/books', methods=['GET'])
# def api_id():
#     # Check if an ID was provided as part of the URL.
#     # If ID is provided, assign it to a variable.
#     # If no ID is provided, display an error in the browser.
#     if 'id' in request.args:
#         id = int(request.args['id'])
#     else:
#         return "Error: No id field provided. Please specify an id."

#     # Create an empty list for our results
#     results = []

#     # Loop through the data and match results that fit the requested ID.
#     # IDs are unique, but other fields might return many results
#     for book in books:
#         if book['id'] == id:
#             results.append(book)

#     # Use the jsonify function from Flask to convert our list of
#     # Python dictionaries to the JSON format.
#     return jsonify(results)

geojson_data = {}
gust_data = {}
    
    
@app.route('/ping_geo',methods=['GET'])
def ping_geo():
    print('ping geo!',datetime.now())
    global geojson_data
    geojson_data = {}
    path = '/home/ksulia/WEFS/freedman-wind-master/app/json/gust_geojson.json'
    if os.path.exists(path):
        with open(path,'r') as f:
            data = json.load(f)
        geojson_data = data
        print('done geo!',datetime.now())
    return {"status":"success geo","time":datetime.now()}

@app.route('/ping_gust',methods=['GET'])
def ping_gust():
    print('ping gust!',datetime.now())
    global gust_data
    gust_data = {}
    path = '/home/ksulia/WEFS/freedman-wind-master/app/json/gust.json'
    if os.path.exists(path):
        with open(path,'r') as f:
            data = json.load(f)
        gust_data = data
        print('done gust!',datetime.now())    
    return {"status":"success gust","time":datetime.now()}


@app.route('/',methods=['GET'])
def geo():
    print('geo',geojson_data.keys(),request.args.get('hour'),geojson_data.keys())
    if len(geojson_data.keys())==0:ping_geo()
    
    hour_req = request.args.get('hour')
    step = 6
    if hour_req == '0': step = 1
    elif hour_req == '1': step = 3
    elif hour_req == '2': step = 6   
    elif hour_req == '3': step = 12

    keys_list = list(geojson_data['geojson'].keys())
    keys_list_subset = [keys_list[i] for i in range(0,len(keys_list),step)]
    print('geo subset', keys_list_subset,geojson_data['marks']['0'],[k for k in range(0,len(geojson_data['marks']),step)])
    mark_obj={}
    for k in range(0,len(geojson_data['marks']),step):
        mark_obj[k] = {'label':geojson_data['marks'][str(k)],
                       'style':{'writing-mode':'vertical-rl','transform':'rotate(-60deg)','transform-origin':'center center'}}
        
    data_temp = {
        'data':{k: geojson_data['data'][k] for k in keys_list_subset},
        'geojson':{k: geojson_data['geojson'][k] for k in keys_list_subset},
        'marks':mark_obj,
        'time':geojson_data['time']
    }
    print('returning geo...') 
    return {'geojson':data_temp}

@app.route('/gust',methods=['GET'])
def gust():
    if len(gust_data.keys())==0:ping_gust()
    print('gust data req',request.args.get('hour'),type(request.args.get('hour')),gust_data.keys(),len(gust_data['gust']['data']))
    
    hour_req = request.args.get('hour')
    step = 6
    if hour_req == '0': step = 1
    elif hour_req == '1': step = 3
    elif hour_req == '2': step = 6   
    elif hour_req == '3': step = 12
        
#     print('step',step)
        
    gust_data_temp = copy.deepcopy(gust_data) # dont overwrite a global variable that you want to keep using!!
    time_data = gust_data_temp['gust']['coords']['Time']['data']  
#     print([time_data[k] for k in range(0,len(time_data),step)])
    gust_data_temp['gust']['coords']['Time']['data'] = [time_data[k] for k in range(0,len(time_data),step)]

    data_temp = {
        'dims':gust_data_temp['gust']['dims'],
        'attrs':gust_data_temp['gust']['attrs'],
        'data':[gust_data_temp['gust']['data'][k] for k in range(0,len(gust_data_temp['gust']['data']),step)],
        'coords':gust_data_temp['gust']['coords'],
        'name':gust_data_temp['gust']['name']
    }
    
    print('returning gust...')
    return {'gust':data_temp}
    
    
    




app.run(host='0.0.0.0', port=7006)
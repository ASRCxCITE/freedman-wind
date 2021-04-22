import flask
from flask import request, jsonify
import os
import json
import pickle as pkl

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
    
    
@app.route('/ping',methods=['GET'])
def ping():
    print('ping!')
    path = '/home/ksulia/WEFS/freedman-wind-master/app/json/gust_geojson.json'
    if os.path.exists(path):
        with open(path,'r') as f:
            data = json.load(f)
#             data = pkl.load(f)
            print('load')
#             data['geojson']=data['geojson'][list(data['geojson'].keys())[0]]
#             data['data']=data['data'][list(data['data'].keys())[0]]
#             print(data.keys())
        print('done')
        
#         data['geojson'][list(data['geojson'].keys())[0]],
#         data['data'][list(data['data'].keys())[0]]
        
        global geojson_data
        geojson_data = data
    return "success"


@app.route('/',methods=['GET'])
def example():
    print(request.args.get('hour'),geojson_data.keys())
    if len(geojson_data.keys())==0:ping()
    
    hour_req = request.args.get('hour')
    step = 6
    if hour_req == 0: step = 1
    elif hour_req == 1: step = 3
    elif hour_req == 2: step = 6   
    elif hour_req == 3: step = 12

    keys_list = list(geojson_data['geojson'].keys())
    keys_list_subset = [keys_list[i] for i in range(0,len(keys_list),step)]
    print(keys_list_subset)
        
    data_temp = {
        'data':{k: geojson_data['data'][k] for k in keys_list_subset[0:1]},
        'geojson':{k: geojson_data['geojson'][k] for k in keys_list_subset[0:1]},
        'marks':geojson_data['marks'],
        'time':geojson_data['time']
    }
    print('returning...')
    return {'geojson':data_temp}
    
    
    




app.run(host='0.0.0.0', port=7006)
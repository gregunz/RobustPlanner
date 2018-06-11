#!/usr/bin/env python
from flask import Flask, jsonify, request
import numpy as np
import os
import pickle

from algo import *
from translation import *
from utils import *
from visualisation import *
from graph import *


app = Flask(__name__)

g = None
stops = []
longLat = dict()
df_risk = None

@app.route('/', methods=['GET'])
def front_end():
    """Return the front-end app"""
    return app.send_static_file('index.html')

@app.route('/api/v1.0/stops', methods=['GET'])
def get_stops():
    res = {
        'stops': stops
    }
    return jsonify(res)


@app.route('/api/v1.0/connections', methods=['GET'])
def get_connections():
    start_time = request.args.get('start_time')
    start_date = request.args.get('start_date')
    start_date = '2017-09-13' #TODO later to be removed
    departure_time = start_date + " " + start_time
    departure_time = pd.to_datetime(departure_time)
    departure_station = request.args.get('departure')
    arrival_station = request.args.get('arrival')
    proba_threshold = request.args.get('certainty')
    proba_threshold = int(proba_threshold[:-1])/100

    connections = []
    try:
        connections = find_path(g, departure_station, arrival_station, departure_time, df_risk, proba_threshold)
    except Exception as e:
        print(e)
        connections = []
    
    connections = connections[::-1]

    def cityFlatten(cityName):
        return [cityName, longLat[cityName][0],longLat[cityName][1]]
    connections = [e for e in map(lambda x: [cityFlatten(x[0]), cityFlatten(x[1]), x[2], x[3], x[4], x[5], x[6]] , connections)]

    res = {
        'connections': connections,
        'code': 500 if connections == [] else 200 
    }

    return jsonify(res)

if __name__ == '__main__':
    #load graph
    print("Loading some files....")
    g = getWalkGraph()
    stops = load_all_stops()
    longLat = load_LongLatDict()
    df_risk = pd.read_pickle('pickle/risk_df2.pkl')
    print("files loaded")
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    

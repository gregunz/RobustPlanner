#!/usr/bin/env python
import os

from flask import Flask, jsonify, request

from graph import *
from run_csa_sbb import run as run_csa, all_stations

app = Flask(__name__)

g = None
stops = []
longLat = dict()
df_risk = None
risk_cache = None


def cityFlatten(cityName):
    return [cityName, longLat[cityName][0],longLat[cityName][1]]

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

@app.route('/api/v1.0/connections_old', methods=['GET'])
def get_connections_old():
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
        connections = find_path(g, departure_station, arrival_station, departure_time, risk_cache[0], proba_threshold)
    except Exception as e:
        print(e)
        connections = []
    
    connections = connections[::-1]
    connections = [e for e in map(lambda x: [cityFlatten(x[0]), cityFlatten(x[1]), x[2], x[3], x[4], x[5], x[6]] , connections)]

    res = {
        'connections': connections,
        'code': 500 if connections == [] else 200 
    }

    return jsonify(res)


@app.route('/api/v1.0/connections', methods=['GET'])
def get_connections():
    departure_station = request.args.get('departure')
    arrival_station = request.args.get('arrival')
    start_time = request.args.get('start_time')
    start_date = request.args.get('start_date')
    departure_timestamp = pd.to_datetime(start_date + " " + start_time).timestamp()
    certainty = request.args.get('certainty')
    certainty = int(certainty[:-1])/100

    speed = 4

    top_n = 5

    csa_sbb = run_csa(
        departure_station=departure_station,
        arrival_station=arrival_station,
        departure_timestamp = departure_timestamp,
        min_certainty = certainty,
        speed = speed,
        top_n = top_n
    )

    paths = csa_sbb.get_paths()

    def edge_to_output(edge):
        start_datetime = pd.to_datetime(start_date).date()
        departure_time = datetime.datetime.fromtimestamp(edge['departure_ts']).time()
        departure_time = datetime.datetime.combine(start_datetime, departure_time)

        arrival_time = datetime.datetime.fromtimestamp(edge['arrival_ts']).time()
        arrival_time = datetime.datetime.combine(start_datetime, arrival_time)

        return [
            cityFlatten(edge['departure_station']),
            cityFlatten(edge['arrival_station']),
            departure_time,
            arrival_time,
            'Walk' if edge['trip_id'] == 'walking' else edge['trip_id'],
            edge['certainty'],
            edge['cum_certainty']
        ]

    def path_to_output(path):
        return [edge_to_output(e) for e in path.edges()]

    if len(paths) == 0:
        res = {
            'code': 500
        }
    else:
        res = {
            'connections': [path_to_output(p) for p in paths],
            'code': 200
        }

    return jsonify(res)






if __name__ == '__main__':
    print("Loading some files....")
    g = getWalkGraph()
    stops = all_stations
    longLat = load_LongLatDict()
    risk_cache = pickle.load(open('pickle/risk_cache.pickle', "rb" ))
    print("files loaded")
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    

#!/usr/bin/env python
import sys
sys.path.insert(0, '../src/')

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
csa_cache = {}


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



@app.route('/api/v1.0/connections', methods=['GET'])
def get_connections():

    res = {
        'code': 500
    }
    try:
        departure_station = request.args.get('departure')
        arrival_station = request.args.get('arrival')
        start_time = request.args.get('start_time')
        start_date = request.args.get('start_date')
        departure_timestamp = pd.to_datetime(start_date + " " + start_time).timestamp()
        certainty = request.args.get('certainty')
        certainty = int(certainty[:-1])/100
        speed = int(request.args.get('speed'))
        top_n = 5

        key = '{}_{}_{}_{}_{}_{}'.format(
            departure_station, start_time, start_date, certainty, speed, top_n
        )
        if key in csa_cache:
            csa_sbb = csa_cache[key]
        else:
            if len(csa_cache) > 10:
                csa_cache.clear()
            csa_sbb = run_csa(
                departure_station=departure_station,
                arrival_station=arrival_station,
                departure_timestamp = departure_timestamp,
                min_certainty = certainty,
                speed = speed,
                top_n = top_n,
                with_tqdm = False
            )
            csa_cache[key] = csa_sbb

        paths = csa_sbb.get_paths(arrival_station)

        def edge_to_output(edge):
            start_datetime = datetime.datetime.fromtimestamp(departure_timestamp)
            departure_time = datetime.datetime.fromtimestamp(edge['departure_ts']).time()
            departure_time = datetime.datetime.combine(start_datetime.date(), departure_time)

            arrival_time = datetime.datetime.fromtimestamp(edge['arrival_ts']).time()
            arrival_datetime = start_datetime
            if start_datetime.time() > arrival_time:
                arrival_datetime += timedelta(days=1)
            arrival_time = datetime.datetime.combine(arrival_datetime.date(), arrival_time)

            return [
                cityFlatten(edge['departure_station']),
                cityFlatten(edge['arrival_station']),
                departure_time,
                arrival_time,
                'Walk' if edge['trip_id'] == 'walking' else edge['trip_id'],
                edge['certainty'],
                edge['cum_certainty'],
                edge['duration']
            ]


        def path_to_output(path, i):
            edges = path.edges()
            first_non_walking_edges = [i for i, e in enumerate(edges) if e['trip_id'] != 'walking']
            start_index = 0 if len(first_non_walking_edges) == 0 else first_non_walking_edges[0]
            real_dep_time = edges[start_index]['arrival_ts'] - edges[start_index]['duration']
            if start_index > 0:
                real_dep_time -= edges[0]['duration']
            path_duration = edges[-1]['arrival_ts'] - real_dep_time
            path_duration = int(path_duration / 60 * 100) / 100
            path_certainty = int(path.last()['cum_certainty'] * 1000) / 10
            path_starting_time = datetime.datetime.fromtimestamp(real_dep_time).strftime('%H:%M')
            path_name = "[#{} at {}] in {} minutes with {}% certainty".format(i+1, path_starting_time, path_duration, path_certainty)
            return [
                [edge_to_output(e) for e in edges],
                path_duration,
                path_name
            ]
        if len(paths) > 0:
            res = {
                'trips': [path_to_output(p, i) for i, p in enumerate(paths)],
                'code': 200
            }
    except Exception as e:
        print(e)

    return jsonify(res)


@app.route('/api/v1.0/connections_dijkstra', methods=['GET'])
def get_connections_dijkstra():
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


if __name__ == '__main__':
    print("Loading some files....")
    g = getWalkGraph()
    stops = all_stations
    longLat = load_LongLatDict()
    risk_cache = pickle.load(open('../pickle/risk_cache.pickle', "rb" ))
    print("files loaded")
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    

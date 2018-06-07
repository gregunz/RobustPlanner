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

@app.route('/', methods=['GET'])
def front_end():
    """Return the front-end app"""
    return app.send_static_file('index.html')

@app.route('/api/v1.0/connections', methods=['GET'])
def get_connections():
    start_time = request.args.get('start_time')
    departure_station = request.args.get('departure')
    arrival_station = request.args.get('arrival')

    departure_time = pd.to_datetime(start_time)
    path = find_path(g, departure_station, arrival_station, departure_time)

    res = {
        'path': path
    }

    return jsonify(res)

if __name__ == '__main__':
    #load graph
    g = getWalkGraph()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

from tqdm import tqdm_notebook as tqdm
tqdm.monitor_interval = 0

import datetime
import pickle

from csa import CSA, Connection
from graph import dist_to_time
from csa_utils import to_departure_time_stamp

print(__name__ + ' loading...')
    
risk_cache = pickle.load(open('pickle/risk_cache.pickle', 'rb'))

nearby_stations_and_dist_cache = pickle.load(open('pickle/nearby_stations_and_dist.pickle', 'rb'))

connections_sbb = pickle.load(open('pickle/connections.pickle', 'rb')) #get_connections_per_day()

all_stations = sorted(list(set([c.dep_station for day in range(7) for c in connections_sbb[day]])))


def run(
    departure_station,
    arrival_station,
    departure_timestamp,
    min_certainty,
    speed,
    top_n,
    with_tqdm = True
):
    
    day = datetime.datetime.fromtimestamp(departure_timestamp).weekday()
    departure_timestamp = to_departure_time_stamp(day, departure_timestamp)
    
    # certainty        
    def get_certainty_sbb(time_delta, trip_id):
        risk = 0.
        for idx, r in risk_cache[day][trip_id]:
            if idx >= time_delta:
                risk = r
                break
        return 1 - risk
    
    # nearby connections
    def get_nearby_connections(dep_station, dep_ts, dist_max = 0.5):
        connections = []
        for arr_station, dist in nearby_stations_and_dist_cache[dep_station]:
            if dist < dist_max:
                arr_ts = dist_to_time(dist, speed=speed).seconds
                connections.append(Connection(dep_station, arr_station, dep_ts, dep_ts + arr_ts, 'walking'))
        return connections

    
    csa_sbb = CSA(
        dep_station=departure_station,
        arr_station=arrival_station,
        dep_ts=departure_timestamp,
        min_certainty=min_certainty,
        get_certainty=get_certainty_sbb,
        get_nearby_connections=get_nearby_connections,
        keep_n = top_n
    )

    walking_connections = get_nearby_connections(csa_sbb.dep_station, csa_sbb.dep_ts)
    
    # First we add walking connections from the departure station 
    for con in walking_connections:
        csa_sbb.add_connection(con)
    
    # Then we add the remaining connections of all the stations 
    # (will add future walking connections on the fly as well)
    if with_tqdm:
        for con in tqdm(connections_sbb[day]):
            csa_sbb.add_connection(con)
    else:
        for con in connections_sbb[day]:
            csa_sbb.add_connection(con)


    return csa_sbb
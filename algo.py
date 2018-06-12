from geopy.distance import distance as geo_dist
from utils import load_metadata
from utils import getLongLat
import pandas as pd
import numpy as np
import datetime

class Station:
    """ Represent all information about a train/bus stations"""
    previous_station: str = '' # from where you arrive
    arrival_time: int = 0 #when you arrived at that station 
    departure_time = 0 #time to leave to that that connection that arrive at station
    trip_id: str = '' #with which trip you arrive at that station
    cumul_success_prob: float = 1.0 #the cumulative proba that the trip fails
    success_prob = 1.0

    def __init__(self, previous_station, departure_time, arrival_time, trip_id, success_proba, cumul_success_prob):
        self.previous_station = previous_station
        self.departure_time = departure_time
        self.arrival_time = arrival_time 
        self.trip_id = trip_id
        self.success_proba = success_proba
        self.cumul_success_prob = cumul_success_prob

#def get_certainty_sbb(time_delta, trip_id):
#    return 1 - get_risk(risk_cache_0, trip_id=trip_id, seconds=time_delta)

def get_risk_fast(risk_cache, trip_id, seconds):
    """
    risk_cache: a datastruct containing the information of delays
    trip_id: trip on which to compute the probability of delay
    seconds: Time you have to take that connection 
    Return the risk in percentage that a the trip is late by the given amount of seconds
    """
    trip_id = trip_id.replace('"', '').replace('\'', '') #safety check
    r = 0
    for idx, risk in risk_cache[trip_id]:
        if idx >= seconds:
            return risk
    return r


# def get_risk(risk_df, row, seconds):
#     """
#     risk_df: Pandas dataframe containing the information of retard
#     row: a list of size 2 [dayOfTheWeek, trip_id]
#     seconds: Time you have to take that connection 
#     Return the risk in percentage that a the trip is late by the given amount of seconds
#     """
#     ecdf = risk_df.loc[row[0], row[1]]
#     ext = np.extract(ecdf.index >= seconds, ecdf)
#     if len(ext) == 0:
#         return 0
#     return ext[0]

def find_path(g, start_station, end_station, departure_time, risk_cache, proba_threshold=0.65):
    """
    g: a Graph object
    start_station: a String representing the Station where you want to start from
    end_station: The satation where you wanna go
    departure_time: time at which you wanna start your journey (usually now)
    risk_cache: a datastruct to compute the probability of failure for each trip
    proba_threshold: Minimal success probability that is allow to be returned

    Return: list of Connection from start_station to end_station that satisfy 
    """
    
    stations = dict()
    q = [] #the queue contains a tuple (station, arrival_time_at_station, trip_id,cumulativ_proba)
    q.append((start_station, departure_time, None, 1.0))
    best_time_end = datetime.datetime.max
    while(len(q)>0):
        q = sorted(q, key=lambda x: x[1]) # extracting the smalest value can be done in O(n) and not in O(n*ln(n))
        #index = q.index(min(q, key=lambda x: x[1]))
        s, time, from_trip, proba = q.pop(0)
        if s in g.stationsConnection:
            allConnection = g.stationsConnection[s]
            for c in allConnection:
                dep, risk = c.nextDeparture(time, proba, proba_threshold, risk_cache, from_trip)
                if dep is not None:
                    #Penalize path where we walk a lot (more than two consecutive times)
                    if from_trip == 'Walk' and dep.trip_id == 'Walk':
                        dep.arrival_time = dep.arrival_time + 5*(dep.arrival_time - dep.departure_time)                
                    if c.toStation == end_station:
                        print('End station founded')
                        best_time_end = dep.arrival_time
                        q = list(filter(lambda x: x[1]<best_time_end, q))                    
                    new_proba = None
                    success_prob = None
                    if from_trip == dep.trip_id:
                        success_prob = 1 
                        new_proba = proba
                    elif dep.trip_id == 'Walk':
                        success_prob = 1
                        new_proba = proba
                    else:
                        success_prob = (1 - risk)
                        new_proba = proba * success_prob
                    
                    if c.toStation not in stations:                          
                        stations[c.toStation] = Station(s, dep.departure_time, dep.arrival_time, dep.trip_id, success_prob, new_proba)
                        q.append((c.toStation, dep.arrival_time, dep.trip_id, new_proba))
                    elif stations[c.toStation].arrival_time > dep.arrival_time:
                        stations[c.toStation] = Station(s, dep.departure_time, dep.arrival_time, dep.trip_id, success_prob, new_proba)
                        q.append((c.toStation, dep.arrival_time, dep.trip_id, new_proba))
        else:
            print("Station not found")
    
    print("Searching path...")
    s = end_station
    connections = [] #from, to, departure_time, arrival_time, trip_id, proba, cumul_proba
    while s != start_station:
        inf_s = stations[s]
        connections.append((inf_s.previous_station,s, inf_s.departure_time, inf_s.arrival_time, inf_s.trip_id, inf_s.success_proba, inf_s.cumul_success_prob))
        s = inf_s.previous_station
    return connections
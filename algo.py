from geopy.distance import distance as geo_dist
from utils import load_metadata
from utils import getLongLat
import pandas as pd
import numpy as np
import datetime


def getAllLine(df, station):
    #Return all the line that pass by this station
    df = df.copy()
    df = df[df['STOP_STATION_NAME'] == station]
    return list(set(df['TRIP_ID']))#list(df['LINE_ID'])

# def getLineID(df, station, time):
#     df = df.copy()
#     df = df[df['STOP_STATION_NAME'] == station][df['DEPARTURE_TIME'] > time]\
#         [df['DEPARTURE_TIME'] < time + pd.Timedelta(minutes=60)]
#     df = df.dropna(subset=['DEPARTURE_TIME'])
#     #df = df[np.isfinite(df['DEPARTURE_TIME'])]
#     return list(df['TRIP_ID'])#list(df['LINE_ID'])
# def viewLine(df, line_id):
#     return df[df["TRIP_ID"] == line_id]#df[df["LINE_ID"] == line_id]
# def dist_between_station(df, station1, station2):
#     df=df.copy()
#     df = df[df['Remark'].isin([station1, station2])]
#     df.index = df['Remark']
#     df = df[['Longitude', 'Latitude']]
#     s1 = df.loc[station1]
#     s2 = df.loc[station2]
#     return geo_dist((s1.Latitude,s1.Longitude), (s2.Latitude,s2.Longitude))
# def getNextStations(df, line_id, station):
#     df = df.copy()
#     df = viewLine(df, line_id)
#     df.index = df['STOP_STATION_NAME']
#     df = df.loc[station:]
#     return df
# def getNextStation(df, line_id, station):
#     df = df.copy()
#     df = getNextStations(df, line_id, station)
#     if df.shape[0] > 1:
#         return df.iloc[1]
#     else:
#         None
# def getNextStationsDetails(df, line_id, station):
#     df = df.copy()
#     df = viewLine(df, line_id)
#     df = df.sort_values('DEPARTURE_TIME')
#     select_next = False
#     nexts = []
#     departure_time = None
#     for index, row in df.iterrows():
#         if select_next:
#             nexts.append((departure_time, row))
#             select_next = False
#         if(row['STOP_STATION_NAME'] == station):
#             if row.DEPARTURE_TIME != np.nan:
#                 select_next = True
#                 departure_time = row.DEPARTURE_TIME
#     return nexts


class Station:
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

def get_risk(risk_df, row, seconds):
    ecdf = risk_df.loc[row[0], row[1]]
    ext = np.extract(ecdf.index >= seconds, ecdf)
    if len(ext) == 0:
        return 0
    return ext[0]

def find_path(g, start_station, end_station, departure_time, df_risk, proba_threshold=0.65):
#WARNING this algo doesnt take into acount if a route is faster but with two hop 
#the queue contains a tuple (station, time at that station)
    stations = dict()
    q = []#queue.Queue()
    q.append((start_station, departure_time, None, 1.0))
    end = False
    best_time_end = datetime.datetime.max
    while(len(q)>0 and not end):
        q = sorted(q, key=lambda x: x[1]) # extracting the smalest value can be done in O(n) and not in O(n*ln(n))
        #index = q.index(min(q, key=lambda x: x[1]))
        s, time, from_trip, proba = q.pop(0)
        if s in g.stationsConnection:
            allConnection = g.stationsConnection[s]
            for c in allConnection:
                dep = c.nextDeparture(time, proba, proba_threshold, df_risk)
                if dep is not None:
                    if c.toStation == end_station:
                        print('End station founded')
                        best_time_end = dep.arrival_time
                        q = list(filter(lambda x: x[1]<best_time_end, q))
                        end = False
                    
                    new_proba = None
                    success_prob = None
                    if from_trip == dep.trip_id:
                        success_prob = 1 
                        new_proba = proba
                    elif dep.trip_id == 'Walk':
                        success_prob = 1
                        new_proba = proba
                    else:
                        success_prob = (1 - get_risk(df_risk, [2, dep.trip_id], (dep.departure_time - time).seconds))
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
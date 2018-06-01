from geopy.distance import distance as geo_dist
#from graph import Graph
from utils import load_metadata
from utils import getLongLat
import pandas as pd
import numpy as np
#geo_dist((lat1, long1), (lat2, long2))geo_dist



def getAllLine(df, station):
    #Return all the line that pass by this station
    df = df.copy()
    df = df[df['STOP_STATION_NAME'] == station]
    #df = df.dropna(subset=['DEPARTURE_TIME'])
    #df = df[np.isfinite(df['DEPARTURE_TIME'])]
    return list(set(df['TRIP_ID']))#list(df['LINE_ID'])

def getLineID(df, station, time):
    df = df.copy()
    df = df[df['STOP_STATION_NAME'] == station][df['DEPARTURE_TIME'] > time]\
        [df['DEPARTURE_TIME'] < time + pd.Timedelta(minutes=60)]
    df = df.dropna(subset=['DEPARTURE_TIME'])
    #df = df[np.isfinite(df['DEPARTURE_TIME'])]
    return list(df['TRIP_ID'])#list(df['LINE_ID'])
def viewLine(df, line_id):
    return df[df["TRIP_ID"] == line_id]#df[df["LINE_ID"] == line_id]
def dist_between_station(df, station1, station2):
    df=df.copy()
    df = df[df['Remark'].isin([station1, station2])]
    df.index = df['Remark']
    df = df[['Longitude', 'Latitude']]
    s1 = df.loc[station1]
    s2 = df.loc[station2]
    return geo_dist((s1.Latitude,s1.Longitude), (s2.Latitude,s2.Longitude))
def getNextStations(df, line_id, station):
    df = df.copy()
    df = viewLine(df, line_id)
    #assumption it is already sorted
    df.index = df['STOP_STATION_NAME']
    df = df.loc[station:]
    return df
def getNextStation(df, line_id, station):
    #print(line_id)
    #print(station)
    df = df.copy()
    df = getNextStations(df, line_id, station)
    if df.shape[0] > 1:
        return df.iloc[1]
    else:
        None
def getNextStationsDetails(df, line_id, station):
    df = df.copy()
    df = viewLine(df, line_id)
    df = df.sort_values('DEPARTURE_TIME')
    select_next = False
    nexts = []
    departure_time = None
    for index, row in df.iterrows():
        if select_next:
            nexts.append((departure_time, row))
            select_next = False
        if(row['STOP_STATION_NAME'] == station):
            if row.DEPARTURE_TIME != np.nan:
                select_next = True
                departure_time = row.DEPARTURE_TIME
    return nexts

#To be run once for all station and result save in a map (or table) 
def getNearByStation(df, station):
    df = df.copy()
    loc = getLongLat(station)
    df = df.dropna(subset=['Remark'])
    df['newDist'] = df.apply(lambda x: geo_dist((x.Latitude, x.Longitude), loc), axis=1)
    df = df[df['newDist'] < 0.1]
    return df

def find_path(g, start_station, end_station, departure_time):
#WARNING this algo doesnt take into acount if a route is faster but with two hop 
#the queue contains a tuple (station, time at that station)
    already_visited = []
    previous_station = dict()
    q = []#queue.Queue()
    df_meta = load_metadata()
    q.append((start_station, departure_time))
    total_dist = dist_between_station(df_meta,start_station, end_station)
    max_dist = total_dist * 1.2
    while(len(q)>0):#(not q.empty()):
        q = sorted(q, key=lambda x: x[1]) # extracting the smalest value can be done in O(n) and not in O(n*ln(n))
        s, time = q.pop(0)
        already_visited.append(s)
        if s in g.stationsConnection:
            allConnection = g.stationsConnection[s] #not taking into account walk connection
            for c in allConnection:
                if c.toStation == end_station:
                    print('End station founded')
                dep = c.nextDeparture(time)
                if dep is not None:
                    dist = dist_between_station(df_meta, c.toStation, end_station)
                    if c.toStation not in previous_station:
                        previous_station[c.toStation] = (s, dep[1])
                    elif previous_station[c.toStation][1] > dep[1]:
                        previous_station[c.toStation] = (s, dep[1])
                        if c.toStation in already_visited:
                            already_visited.remove(c.toStation)
                    if c.toStation not in already_visited and\
                        dist < max_dist:
                        already_visited.append(c.toStation)
                        q.append((c.toStation, dep[1])) #dep[1] is arrival time
                    if c.toStation in already_visited:
                        ##We should check that we are not arriving earlier if so then we need to recompute a path
                        ##it's good to check if time is before otherwise we could create cycle
                        ##even if its not the best way to do at least we dont have cycle
                        #if we arrive earlier at that station then we change the previous station for that station 
                        #as for each station we maintain a list of the previous station 
                        #print("revisiting " + c.toStation)
                        pass
        else:
            print("Scheiss")
    
    print("Searching path...")
    s = end_station
    path = []
    while s != start_station:
        path.append(s)
        s = previous_station[s][0]
    path.append(s)
    return path
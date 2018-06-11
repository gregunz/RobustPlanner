from utils import get_all_stops, load_LongLatDict
from tqdm import tqdm_notebook as tqdm
from datetime import timedelta
from itertools import groupby
from operator import itemgetter
from algo import *
import pickle

class Departure():
    departure_time = 0
    arrival_time = 0
    trip_id = ''

    def __init__(self, departure_time, arrival_time, trip_id):
        self.departure_time = departure_time
        self.arrival_time = arrival_time
        self.trip_id = trip_id

class ByWalkConnection():
    toStation = ""
    distance = 0 #in km

    def __init__(self, stationName, dist):
        self.toStation = stationName
        self.distance = dist
    
    def nextDeparture(self, time, current_proba, proba_threshold, df_risk):
        return Departure(time, time + dist_to_time(self.distance), 'Walk')

class Connection():
    toStation = "" #Station to which we are connected
    departures = [] #(dep_time,arrival_time) assume sorted by arrival time
    
    def __init__(self, stationName, dep):
        self.toStation = stationName
        self.departures = dep
    
    def nextDeparture(self, time, current_proba, proba_threshold, df_risk):
        for dep in self.departures:
            if dep.departure_time >= time:
                risk = get_risk(df_risk, [2, dep.trip_id], (dep.departure_time - time).seconds)
                if proba_threshold < current_proba*(1 - risk):
                    return dep
    
class Graph():
    stationsConnection = dict() #(String -> connectedStation)
    def __init__(self,stationsConnection):
        self.stationsConnection = stationsConnection


def dist_to_time(dist, speed=4):
    """
    dist: Distance in km
    speed: Speed is in km per hour (kmh)
    Return: Time as a delta time object """
    time = dist / speed
    return timedelta(hours=time)


def addDepartureToGraph(g, from_station, to_station, departure):
    if from_station in g.stationsConnection:
        neighbours = g.stationsConnection[from_station]
        neighbours_found = False
        for n in neighbours:
            if n.toStation == to_station:
                n.departures.append(departure)
                n.departures = sorted(n.departures, key=lambda x: x.arrival_time)
                neighbours_found = True
        if not neighbours_found:
            neighbours.append(Connection(to_station, [departure]))
    else:
        g.stationsConnection[from_station] = [Connection(to_station, [departure])]

def buildGraph(df, allStation = []):
    """
    Create a graph for the whole network or only a subset if the argument allStation is provided
    """
    g = Graph(dict())
    for name, group in tqdm(df.groupby('TRIP_ID')):
        group = group.sort_values('DEPARTURE_TIME')
        departure_time = -1
        departure_station = None
        for row_number, row in group.iterrows():
            if departure_time != -1:
                d = Departure(departure_time, row.ARRIVAL_TIME, row.TRIP_ID)
                addDepartureToGraph(g, departure_station, row.STOP_STATION_NAME, d)
            departure_time = row.DEPARTURE_TIME
            departure_station = row.STOP_STATION_NAME
    return g

def getNearByStation(station, allStations, tr_station2long, distMax=0.3):
    loc = tr_station2long[station]
    closeStation = []
    for s in allStations:
        loc2 = tr_station2long[s]
        dist = geo_dist(loc, loc2).km
        if dist <= distMax:
            closeStation.append((s, dist))
    return closeStation

def updateGraphWithWalk(g):
    """
    WARNING this method should not be call more than once
    """
    tr = load_LongLatDict()
    allStation = get_all_stops()

    for s in tqdm(allStation):
        nearStations = getNearByStation(s, allStation, tr, distMax=0.5)
        nearConnection = list(map(lambda x: ByWalkConnection(x[0], x[1]), nearStations))
        if s in g.stationsConnection:
            g.stationsConnection[s] = g.stationsConnection[s] + nearConnection 
        else:
            g.stationsConnection[s] = nearConnection
    pickle.dump(g, open("pickle/graph_walk.p", "wb" ))
    return g


def getGraph():
    return pickle.load(open("pickle/graph.p", "rb" ))
def getWalkGraph():
    return pickle.load(open("pickle/graph_walk.p", "rb" ))
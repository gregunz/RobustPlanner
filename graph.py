from utils import get_all_stops
from tqdm import tqdm_notebook as tqdm
from itertools import groupby
from operator import itemgetter
from algo import *
import pickle

class StationConnections():
    connections = dict()
    walkConnections = dict()
    
    
class ByWalkConnection():
    toStation:str = ""
    distance:int = 500 #in metres
    
    
class Connection():
    toStation:str = "" #Station to which we are connected
    departures = [] #(dep_time,arrival_time) assume sorted by arrival time
    
    def __init__(self, stationName, dep):
        self.toStation = stationName
        self.departures = dep
    
    def nextDeparture(self, time):
        for dep in self.departures:
            if dep[0] >= time:
                return dep
    
class Graph():
    stationsConnection = dict() #(String -> connectedStation)
    def __init__(self,stationsConnection):
        self.stationsConnection = stationsConnection

def buildGraph(df, allStation = []):
    """
    Create a graph for the whole network or only a subset if the argument allStation is provided
    """
    key_func = lambda x: x[0]
    stationsConnection = dict()
    if len(allStation) == 0:
        allStation = get_all_stops()
    for s in tqdm(allStation):
        print(s)
        lines = getAllLine(df,s)
        nexts = []
        for l in lines:
            next_ = getNextStationsDetails(df, l, s)
            next_ = list(map(lambda n: (n[1].STOP_STATION_NAME, (n[0], n[1].ARRIVAL_TIME)), next_)) #add expected delay and variance
            nexts = nexts + next_
        nexts = sorted(nexts, key=key_func)
        nexts_stations = [Connection(key, sorted([e[1] for e in group], key=lambda x: x[1])) \
                    for key, group in groupby(nexts, key_func)]
        stationsConnection[s] = nexts_stations
    g = Graph(stationsConnection)
    pickle.dump(g, open("pickle/graph.p", "wb" ))
    return g

def getGraph():
    return pickle.load(open("pickle/graph.p", "rb" ))
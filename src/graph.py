from utils import get_all_stops, load_LongLatDict
from tqdm import tqdm_notebook as tqdm
from datetime import timedelta
from dijkstra import *
import pickle

class Departure():
    """
    Contains all the information about a departure from a station A to a station B
    """
    departure_time = 0
    arrival_time = 0
    trip_id = ''

    def __init__(self, departure_time, arrival_time, trip_id):
        self.departure_time = departure_time
        self.arrival_time = arrival_time
        self.trip_id = trip_id

class ByWalkConnection():
    """ Represent a Conection where the user walk to the next Station
    """
    toStation = ""
    distance = 0 #in km

    def __init__(self, toStation, dist):
        """
        toStation: the station that is connected
        dist: distance in km
        """
        self.toStation = toStation
        self.distance = dist
    
    def nextDeparture(self, time, current_proba, proba_threshold, risk_cache, from_trip):
        """
        Args:
            time: datetime when you are at station A
            current_proba: probability of success before taking that connection
            proba_threshold: minimum probability of success that must still hold after taking that connection
            risk_cache: a datastruct to compute the probability of failure for each trip
            from_trip: trip_id from the previous connection
        =========================================================
        Return: a tuple (Departure, failure_proba) reprensenting the next departure possible that meet the constraint
        """
        return Departure(time, time + dist_to_time(self.distance), 'Walk'), 0.0

class Connection():
    """ Represent a Conection to a Station B
    """
    toStation = "" #Station to which we are connected
    departures = [] #(dep_time,arrival_time) assume sorted by arrival time
    
    def __init__(self, stationName, dep):
        """
        toStation: the station that is connected
        dist: distance in km
        """
        self.toStation = stationName
        self.departures = dep
    
    def nextDeparture(self, time, current_proba, proba_threshold, risk_cache, from_trip):
        """
        Args:
            time: datetime when you are at station A
            current_proba: probability of success before taking that connection
            proba_threshold: minimum probability of success that must still hold after taking that connection
            risk_cache: a datastruct to compute the probability of failure for each trip
            from_trip: trip_id from the previous connection
        =========================================================
        Return: a tuple (Departure, failure_proba) reprensenting the next departure possible that meet the constraint
        """
        for dep in self.departures:
            departure_time = dep.departure_time
            if dep.trip_id != from_trip:
                #add a minimal time to make a change
                departure_time = departure_time - datetime.timedelta(minutes=0)
            if departure_time >= time:              
                if dep.trip_id == from_trip or from_trip == 'Walk' or from_trip == None:
                    risk = 0.0
                else:
                    risk = get_risk_fast(risk_cache, from_trip, (departure_time - time).seconds)
                if proba_threshold <= current_proba * (1-risk):
                    return dep, risk
        return None, None
    
class Graph():
    """ Contains all the travel connection for a given day of the week"""
    stationsConnection = dict() #(String -> connectedStation)
    def __init__(self,stationsConnection):
        self.stationsConnection = stationsConnection


def dist_to_time(dist, speed=4):
    """
    Args:
        dist: Distance in km
        speed: Speed is in km per hour (kmh)
    =====================================
    Return: Time as a delta time object """
    time = dist / speed
    return timedelta(hours=time)


def addDepartureToGraph(g, from_station, to_station, departure):
    """ Insert a Departure into the graph
    Args:
        g: Graph representing the network, this object is updated
        from_station: the station where to add the connection (Departure)
        to_station: neighbours of from_station 
        departure: a Departure object
    ===========================================
    Return: None (the graph g in updated)
    """
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

def buildGraph(df):
    """
    Create a graph for the whole network
    Args:
        df: a Dataframe containing all the trip in one day
    =======================
    Return: A Graph object containing the train/bus connection only (No walking connection)
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
    """ get the nearby stations that we can reach by walk
    Args:
        station: station from which we start
        allStation: list of all the stations to compare to station
        tr_station2long: a dict that map a station:str to a pair of (longiture, latitude)
        distMax: threshold that set the maximal distance from
    ===============================
    Return: list of tuple (station, dist) for 
        stations that are at max distMax of the base station.
    """
    loc = tr_station2long[station]
    closeStation = []
    for s in allStations:
        loc2 = tr_station2long[s]
        dist = geo_dist(loc, loc2).km
        if dist <= distMax:
            closeStation.append((s, dist))
    return closeStation

def updateGraphWithWalk(g):
    """ Given a graph it adds the walking connection to it
    Args:
        g: a Graph object to update
    =====================
    Return: None
    WARNING this method should not be call more than once
    """
    tr = load_LongLatDict()
    allStation = g.stationsConnection.keys()

    for s in tqdm(allStation):
        nearStations = getNearByStation(s, allStation, tr, distMax=0.5)
        nearConnection = list(map(lambda x: ByWalkConnection(x[0], x[1]), nearStations))
        if s in g.stationsConnection:
            g.stationsConnection[s] = g.stationsConnection[s] + nearConnection 
        else:
            g.stationsConnection[s] = nearConnection
    pickle.dump(g, open("../pickle/graph_walk.p", "wb" ))
    return g


def getGraph():
    """
    Return: a precomputed graph without the walk connection
    """
    return pickle.load(open("../pickle/graph.p", "rb" ))
def getWalkGraph():
    """
    Return: a precomputed graph with the walk connection added
    """
    return pickle.load(open("../pickle/graph_walk.p", "rb" ))
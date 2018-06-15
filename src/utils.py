from geopy.distance import distance as geo_dist
import pandas as pd
from translation import translate
import pickle

def load_data(file, translated = False):
    """Load data from the cvs file
    Args:
        file: the file path of the csv file
        translated: a boolean set to True if you want the return dataframe to be translated into english
    Return: A Pandas dataframe with the correct type for the columns
    """
    parse_dates = ['BETRIEBSTAG', 'ANKUNFTSZEIT', 'AN_PROGNOSE', "ABFAHRTSZEIT", "AB_PROGNOSE"]
    dtypes = {
        "FAHRT_BEZEICHNER": 'str',
        "LINIEN_ID": 'str',
        "LINIEN_TEXT": 'str',
        "UMLAUF_ID": 'str',
        "VERKEHRSMITTEL_TEXT": 'str'
    }
    df = pd.read_csv(file, sep=";", dtype = dtypes,
                         parse_dates= parse_dates)
    if translated:
        return translate(df)
    else:
        return df

def store_all_stops():
    """ Save the list of all stations into a pickle file
    """
    stops = get_all_stops()
    pickle.dump(stops, open("../pickle/stops.p", "wb" ))
def load_all_stops():
    """Load the list of all stations from the pickle file created by store_all_stops()
    """
    return pickle.load(open("../pickle/stops.p", "rb" ))

def store_LongLatDict():
    """Save a dict mapping station name to (Longitude, Latitude)
    """
    d = createLongLatDict()
    pickle.dump(d, open("../pickle/longLatDict.p", "wb" ))

def load_LongLatDict():
    """Load a dict mapping station name to (Longitude, Latitude)
    """
    return pickle.load(open("../pickle/longLatDict.p", "rb" ))

def get_all_stops():
    """
    Return: a list the satation name located at less than 10km from Zürich HB
    """
    metadata_df = load_metadata()
    zurichHB = metadata_df[metadata_df.Remark == "Zürich HB"].iloc[0]
    metadata_df = metadata_df.dropna(subset=['Latitude', 'Longitude'])
    metadata_df["dist"] = metadata_df.apply(lambda x: geo_dist((zurichHB.Latitude,zurichHB.Longitude), (x.Latitude,x.Longitude)), axis=1)
    zurich_stops_df = metadata_df[metadata_df["dist"] < 10]
    return list(zurich_stops_df['Remark'])
    
def getLongLat(station):
    """Return the Longitude and Latitude for a given station"""
    meta_df = load_metadata()
    meta_df.index = meta_df['Remark']
    s1 = meta_df.loc[station]
    return (s1.Latitude,s1.Longitude)

def createLongLatDict():
    """
    Return a dict that map a station name to a (Long, Lat) tupple
    """
    meta_df = load_metadata()
    meta_df.index = meta_df['Remark']
    d = dict()
    for stat in meta_df['Remark'].values:
        s = meta_df.loc[stat]
        d[stat] = [s.Latitude,s.Longitude]
    return d

# def dist_between_stations(station1, station2):
#     #TODO optimize such that we dont need to read two times the metadata file
#     return geo_dist(getLongLat(station1), getLongLat(station2))
    
def filter_zurich_data(df):
    """
    Args:
        df: Dataframe of the connections
    Return:
        The same dataframe for stations that are only up to 10km from Zurich HB
    """
    zurich_stops = get_all_stops()
    return df[df['STOP_STATION_NAME'].isin(zurich_stops)]

def load_metadata():
    """
    Open the meta data csv file
    Return:
        A pandas Dataframe containing all the metadata info
    """
    with open("data/metadata/BFKOORD_GEO") as file:
        metadata = file.readlines()
    
    metadata_cleaned = [line.split("%") for line in metadata]
    metadata_cleaned = [[line[0].split(), line[1][1:-1]] for line in  metadata_cleaned]
    metadata_cleaned = [[line[0][0], line[0][1], line[0][2], line[0][3], line[1]] for line in metadata_cleaned]

    metadata_df = pd.DataFrame(metadata_cleaned, columns=["StationID", "Longitude", "Latitude", "Height", "Remark"])

    metadata_df["Longitude"] = pd.to_numeric(metadata_df["Longitude"])
    metadata_df["Latitude"] = pd.to_numeric(metadata_df["Latitude"])
    return metadata_df

def to_timestamp(x, date_format):
    '''
        Transform a date to its timestamp given a date_format.
        NaN values are mapped to -99999
    '''
    if pd.isnull(x):
        return -99999
    else:
        return time.mktime(datetime.datetime.strptime(x, date_format).timetuple())


def time_diff(x, y):
    '''
        Compute the time difference between two values.
    '''
    if (x == -99999) & (y == -99999):
        return -99999
    elif (x == -99999) | (y == -99999):
        return 0
    else:
        return y - x


def get_day(x):
    if pd.isnull(x):
        return -1
    else:
        return datetime.datetime.strptime(x, "%d.%m.%Y").weekday()
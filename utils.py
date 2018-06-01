from geopy.distance import distance as geo_dist
import pandas as pd
from translation import translate

def load_data(file, translated = False):
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

def get_all_stops():
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

def dist_between_stations(station1, station2):
    #TODO optimize such that we dont need to read two times the metadata file
    return geo_dist(getLongLat(station1), getLongLat(station2))
    
def filter_zurich_data(df):
    zurich_stops = get_all_stops()
    return df[df['STOP_STATION_NAME'].isin(zurich_stops)]

def load_metadata():
    with open("data/metadata/BFKOORD_GEO") as file:
        metadata = file.readlines()
    
    metadata_cleaned = [line.split("%") for line in metadata]
    metadata_cleaned = [[line[0].split(), line[1][1:-1]] for line in  metadata_cleaned]
    metadata_cleaned = [[line[0][0], line[0][1], line[0][2], line[0][3], line[1]] for line in metadata_cleaned]

    metadata_df = pd.DataFrame(metadata_cleaned, columns=["StationID", "Longitude", "Latitude", "Height", "Remark"])

    metadata_df["Longitude"] = pd.to_numeric(metadata_df["Longitude"])
    metadata_df["Latitude"] = pd.to_numeric(metadata_df["Latitude"])
    return metadata_df
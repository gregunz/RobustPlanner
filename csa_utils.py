import pandas as pd
import datetime
from csa import Connection

print(__name__ + ' loading...')

def get_connections(day):
    df_connections = pd.read_csv('links/links_{}.csv'.format(day), header=None)
    return df_connections.apply(lambda x: Connection(*x), axis=1).values.tolist()

def get_connections_per_day():
    sbb_connections = {}
    for day in range(7):
        sbb_connections[day] = get_connections(day)
    return sbb_connections

def to_departure_time_stamp(day, ts):
    date = datetime.date(2018, 1, 8 + day)
    time = datetime.datetime.fromtimestamp(ts).time()
    return datetime.datetime.combine(date, time).timestamp()
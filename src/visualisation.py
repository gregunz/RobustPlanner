import folium
from utils import load_LongLatDict

def showStation(stations, markers = []):
    """ Show a map with all the stations
    """
    loc = load_LongLatDict()['Zürich HB']
    my_map = folium.Map(location=loc)
    for m in markers:
        folium.Marker(getLongLat(m), popup=m).add_to(my_map)
    for s in stations:
        l = getLongLat(s)
        folium.RegularPolygonMarker(
            l,
            popup=s,
            fill_color='#132b5e',
            number_of_sides=3,
            radius=3
        ).add_to(my_map)
    return my_map

def showPath(path):
    """ Show a map with a path draw on it
    """
    dict_long_lat = load_LongLatDict()
    loc = dict_long_lat['Zürich HB']
    my_map = folium.Map(location=loc)
    for p in path:
        p1_ = dict_long_lat[p[0]]
        p2_ = dict_long_lat[p[1]]
        folium.PolyLine(locations=[p1_, p2_], color='blue').add_to(my_map)
    return my_map
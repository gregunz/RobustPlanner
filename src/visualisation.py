import folium
from utils import getLongLat

def showStation(stations, markers = []):
    """ Show a map with all the stations
    """
    loc = getLongLat('Zürich HB')
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
    loc = getLongLat('Zürich HB')
    my_map = folium.Map(location=loc)
    p1 = path[:-1]
    p2 = path[1:]
    for i in range(len(p1)):
        p1_ = getLongLat(p1[i])
        p2_ = getLongLat(p2[i])
        folium.PolyLine(locations=[p1_, p2_], color='blue').add_to(my_map)
    return my_map
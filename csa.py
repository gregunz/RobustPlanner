from copy import copy
import pickle

print(__name__ + ' loading...')

class Connection:
    def __init__(self, dep_station, arr_station, dep_ts, arr_ts, trip_id):
        self.dep_station = dep_station
        self.arr_station = arr_station
        self.dep_ts = dep_ts
        self.arr_ts = arr_ts
        self.trip_id = trip_id

    def get_duration(self):
        return self.arr_ts - self.dep_ts

    def __lt__(self, other):
        return self.dep_ts < other.dep_ts

    def __str__(self):
        return 'FROM={}, TO={}, START={}, END={} ({})' \
            .format(self.dep_station, self.arr_station, self.dep_ts, self.arr_ts, self.trip_id, self.trip_id)

class History:
    def __init__(self, station, arr_ts, duration, cum_certainty, trip_id):
        d = self.to_dict(station, arr_ts, duration, cum_certainty, trip_id)
        self.hist = [d]

    def copy(self):
        new_hist = copy(self)
        new_hist.hist = self.hist.copy()
        return new_hist

    def add(self, station, arr_ts, duration, cum_certainty, trip_id):
        self.hist.append(self.to_dict(station, arr_ts, duration, cum_certainty, trip_id))

    def to_dict(self, station, arr_ts, duration, cum_certainty, trip_id):
        return {
            'station': station,
            'arr_ts': arr_ts,
            'duration': duration,
            'cum_certainty': cum_certainty,
            'trip_id': trip_id,
        }

    def last(self):
        return self.hist[-1]

    def edges(self):
        edges = []
        certainty = None
        for dep, arr in zip(self.hist[:-1], self.hist[1:]):
            if certainty is None or dep['trip_id'] != arr['trip_id']:
                certainty = arr['cum_certainty'] / dep['cum_certainty']
            d = {
                'departure_station': dep['station'],
                'arrival_station': arr['station'],
                'departure_ts': dep['arr_ts'],
                'arrival_ts': arr['arr_ts'],
                'duration': arr['duration'],
                'certainty': certainty,
                'cum_certainty': dep['cum_certainty'],
                'departure_cum_certainty': arr['cum_certainty'],
                'trip_id': arr['trip_id'],
            }
            edges.append(d)
        return edges



class OneWay:
    def __init__(self, arr_station, arr_ts, duration, cum_certainty, trip_id):
        self.arr_station = arr_station
        self.arr_ts = arr_ts
        self.duration = duration
        self.cum_certainty = cum_certainty
        self.hist = History(arr_station, arr_ts, duration, cum_certainty, trip_id)

    def copy(self):
        new_way = copy(self)
        new_way.hist = self.hist.copy()
        return new_way

    def add(self, arr_station, arr_ts, duration, cum_certainty, trip_id):
        self.arr_ts = arr_ts
        self.cum_certainty = cum_certainty
        self.hist.add(arr_station, arr_ts, duration, cum_certainty, trip_id)

    def last_trip_id(self):
        for h in self.hist.hist[::-1]:
            if h['trip_id'] != 'walking':
                return h['trip_id']
        print('something wrong occured')

    def is_faster(self, other):
        return self.arr_ts < other.arr_ts

    def is_safer(self, other):
        return self.cum_certainty > other.cum_certainty

    def __lt__(self, other):
        return self.is_faster(other) or (self.arr_ts == other.arr_ts and self.cum_certainty > other.cum_certainty)

    def __str__(self):
        return 'arr_ts={}, cum_certainty={}, num_node={}' \
            .format(self.arr_ts, self.cum_certainty, len(self.hist.hist))


class Trajectory:
    def __init__(self, way):
        self.ways = [way]

    def update(self, new_way, keep_n):
        self.ways.append(new_way)
        self.ways = sorted(self.ways)
        prev_w = self.ways[0]

        new_ways = [self.ways[0]]
        for w in self.ways[1:]:
            if len(new_ways) >= keep_n:
                break
            if w.is_safer(prev_w):
                new_ways.append(w)
                prev_w = w

        self.ways = new_ways

    def ts_to_beat(self, keep_n):
        if len(self.ways) > 0 and len([w for w in self.ways if w.cum_certainty == 1]) > 0:
            return [w for w in self.ways if w.cum_certainty == 1][0].arr_ts
        elif len(self.ways) < keep_n:
            return 2e30
        else:
            return self.ways[keep_n - 1].arr_ts



class CSA:
    def __init__(self, dep_station, arr_station, dep_ts, min_certainty, get_certainty, get_nearby_connections, keep_n=3):
        self.dep_station = dep_station
        self.arr_station = arr_station
        self.dep_ts = dep_ts
        self.real_dep_ts = None
        self.min_certainty = min_certainty
        self.best_trajectories = {dep_station: Trajectory(OneWay(dep_station, dep_ts, 0, 1, 'start'))}
        self.get_certainty = get_certainty
        self.get_nearby_connections = get_nearby_connections
        self.keep_n = keep_n

    def add_connection(self, con, add_walking = True):
        add_walking = add_walking and con.trip_id != 'walking'
        if con.dep_station in self.best_trajectories\
            and (self.real_dep_ts is None or con.arr_ts - self.real_dep_ts < 3 * 3600):
            dep_traj = self.best_trajectories[con.dep_station]
            if con.arr_station in self.best_trajectories:
                time_to_beat = self.best_trajectories[con.arr_station].ts_to_beat(self.keep_n)
            else:
                time_to_beat = 2e30
            if con.arr_ts < time_to_beat:
                for prev_way in dep_traj.ways:
                    time_delta = con.dep_ts - prev_way.arr_ts
                    if time_delta >= 0:
                        new_cum_certainty = prev_way.cum_certainty
                        if con.trip_id != prev_way.last_trip_id() \
                                and prev_way.last_trip_id() != 'start' \
                                and con.trip_id != 'walking':
                            new_cum_certainty *= self.get_certainty(time_delta, prev_way.last_trip_id())
                        if new_cum_certainty >= self.min_certainty:
                            if con.dep_station == self.dep_station:
                                prev_way.arr_ts = con.dep_ts
                                if self.real_dep_ts is None and con.trip_id != 'walking':
                                    self.real_dep_ts = con.dep_ts
                            new_way = prev_way.copy()
                            new_way.add(con.arr_station, con.arr_ts, con.get_duration(), new_cum_certainty, con.trip_id)
                            if con.arr_station not in self.best_trajectories:
                                self.best_trajectories[con.arr_station] = Trajectory(new_way)
                                if add_walking:
                                    self.__add_walk_cons(con.arr_station, con.arr_ts)
                            else:
                                if new_way.is_faster(self.best_trajectories[con.arr_station].ways[0]) and add_walking:
                                    self.__add_walk_cons(con.arr_station, con.arr_ts)
                                self.best_trajectories[con.arr_station].update(new_way, self.keep_n)

    def __add_walk_cons(self, dep_station, dep_ts):
        nearby_cons = self.get_nearby_connections(dep_station, dep_ts)
        for c in nearby_cons:
            self.add_connection(c)

    def get_ways(self, station=None):
        if station is None:
            station = self.arr_station
        if station not in self.best_trajectories:
            return []
        return self.best_trajectories[station].ways

    def get_paths(self, station=None):
        if station is None:
            station = self.arr_station
        return [w.hist for w in self.get_ways(station)]


def debug(csa):
    print('FROM: {}'.format(csa.dep_station))
    for dep_station, trajectory in csa.best_trajectories.items():
        if dep_station != csa.dep_station:
            print('  TO: {}'.format(dep_station))
            for i, w in enumerate(trajectory.ways):
                print('  ({}) {}'.format(i+1, w))

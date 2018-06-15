import matplotlib.pyplot as plt
import numpy as np
import datetime
import pandas as pd

def plot_risk_of_lateness(ecdf_data, title=""):
    plt.figure(figsize=(20, 4))
    plt.plot(ecdf_data.keys(), ecdf_data.values)
    plt.xlabel("seconds")
    plt.ylabel("risk of being late")
    plt.title(title)
    plt.show()

def plot_risk_of_lateness_per_day(transport, trip_id, interval=60):
    plt.figure(figsize=(20,4))

    for sec in range(0, interval*5, interval):
        plt.bar(np.asarray(range(7)) -0.3 + 0.15*int(sec/interval), [transport.loc[:,:sec].loc[i].iloc[-1] for i in range(7)], width=0.1)

    plt.xticks(range(7), ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
    plt.title("Risk of being late for TRIP_ID = %s per days" % trip_id)
    plt.ylabel("Risk of being more than m minutes late")
    plt.legend(["%s sec" % i for i in range(0, interval * 5, interval)])

    plt.show()

def pretty_print_csa_sbb(csa_sbb, s):
    print()
    print('{} -> {}'.format(csa_sbb.dep_station, s))
    print()
    for i, path in enumerate(csa_sbb.get_paths(s)):
        first_non_walking_edges = [i for i, e in enumerate(path.edges()) if e['trip_id'] != 'walking']
        start_index = 0 if len(first_non_walking_edges) == 0 else first_non_walking_edges[0]
        path_duration = path.edges()[-1]['arrival_ts'] - path.edges()[start_index]['arrival_ts']
        path_duration += path.edges()[start_index]['duration']
        if start_index > 0:
            path_duration += path.edges()[0]['duration']
        path_duration = int(path_duration / 60 * 1000) / 1000
        path_certainty = int(path.last()['cum_certainty'] * 1000) / 1000
        path_starting_time = datetime.datetime.fromtimestamp(path.edges()[start_index]['departure_ts']).strftime('%H:%M')
        path_name = "[#{} at {}] in {} minutes with {} certainty".format(i+1, path_starting_time, path_duration, path_certainty)
        print(path_name)
        print()
        lines = [['FROM', 'TO', 'DURATION', 'CERTAINTY', 'TRIP_ID']]
        for e in path.edges():
            line = [e['departure_station'], e['arrival_station'], int(e['duration'] / 60 * 100) / 100 , int(e['certainty'] * 100) / 100, e['trip_id']]
            line = [str(e) for e in line]
            lines.append(line)
        col_widths = [max([len(word) for word in row]) + 2 for row in pd.DataFrame(lines).T.values ]  # padding
        for row in lines:
            print(''.join(word.ljust(col_widths[i]) for i, word in enumerate(row)))
        print()

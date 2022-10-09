#!/usr/bin/python
# -*- coding: utf-8 -*-
import argparse
import csv
import json
from pprint import pprint
from datetime import datetime, timedelta

parser = argparse.ArgumentParser(description='Python weekend entry task')
parser.add_argument('csv_file_path', help='Relative path of the csv dataset file', type=str)
parser.add_argument('origin', help='Airport A', type=str)
parser.add_argument('destination', help='Airport B', type=str)
parser.add_argument('-b', '--bags', help='Number of bags. If not specified, it is assumed that the user has no bags.', type=int)
parser.add_argument('-R', '--return', dest='round', help='If the user returns back to origin.', action='store_true')
parser.add_argument('-l', '--min-layover-time', help='Minimum layover hours accepted.', type=int, default=1)
parser.add_argument('-L', '--max-layover-time', help='Maximum layover hours accepted.', type=int, default=6)
parser.add_argument('-d', '--depart-day', help='Day to start flyign to destination in format YYYY-MM-DD.', type=str)
parser.add_argument('-r', '--return-day', help='Day to start flyign back to origin in format YYYY-MM-DD, if there is a return trip.', type=str)
parser.add_argument('-s', '--stops', help='Maximum number of stops.', type=int)
parser.add_argument('-or', '--outbound-range', help='Time range of accepted outbound departure flight times in format HH:MM:SS-HH:MM:SS.', type=str)
parser.add_argument('-rr', '--return-range', help='Time range of accepted return departure flight times in format HH:MM:SS-HH:MM:SS.', type=str)
parser.add_argument('-t', '--trip-duration', help='Maximum trip duration in hours (A -> B). For round trips it is the maximum time of any of both trips, using Skyscanner\'s standard.', type=float)
parser.add_argument('-f', '--file', help='Save results to file results.json.', action='store_true')
args = parser.parse_args()


def main():
    parse_ranges()
    raw_data = read_csv_file(args.csv_file_path)
    if not args.round:
        results = find_flights(raw_data, args.origin, args.destination)
    else:
        results = build_round_trip_combinations(
            find_flights(raw_data, args.origin, args.destination), 
            find_flights(raw_data, args.destination, args.origin, True))
    print_combinations(results)        
    pprint(results)
    if args.file:
        with open('results.json', 'w') as f:
            json.dump(results, f, indent=4, sort_keys=True)


def find_flights(data, origin, destination, is_return=False) -> list:
    """ Find all possible combinations of flights in data from origin to destination """
    global combinations
    combinations = []
    filtered_data = clean_bad_flights(json.loads(json.dumps(data)),
                                      bags=args.bags,
                                      airport_A=destination,
                                      airport_B=origin,
                                      departure_min=return_range[0] if is_return else outbound_range[0],
                                      departure_max=return_range[1] if is_return else outbound_range[1],)
    recursive_search(filtered_data, origin, destination, [])
    return sorted(combinations, key=lambda k: k['total_price'])


def clean_bad_flights(data, bags=None, airport_A=None, airport_B=None, departure_min=None, departure_max=None) -> list:
    """ 
    Remove flights that fulfill any of the following conditions:
    a) allow less bags than the user has
    b) include the airport_A as origin or airport_B as destination
    c) have a departure time before the minimum accepted departure time
    d) have a departure time after the maximum accepted departure time
    """
    for flight in json.loads(json.dumps(data)):
        if (bags is not None and flight['bags_allowed'] < str(bags)) \
            or (airport_A is not None and airport_A == flight['origin']) \
            or (airport_B is not None and airport_B == flight['destination']) \
            or (departure_min is not None and len(departure_min) > 8 and flight['departure'] < departure_min) \
            or (departure_min is not None and len(departure_min) == 8 and flight['departure'][-8:] < departure_min) \
            or (departure_max is not None and len(departure_max) > 8 and flight['departure'] > departure_max) \
            or (departure_max is not None and len(departure_max) == 8 and flight['departure'][-8:] > departure_max):
            data.remove(flight)
    return data


def recursive_search(data, origin, destination, flights_used) -> None:
    """ Recursive function to find all possible combinations of flights from origin to destination """
    global combinations
    for flight in data:
        if flight['origin'] == origin:
            flight['base_price'] = float(flight['base_price'])
            flight['bag_price'] = float(flight['bag_price'])
            flight['bags_allowed'] = int(flight['bags_allowed'])
            flights_used.append(flight)
            travel_time = datetime.strptime(flight['arrival'], '%Y-%m-%dT%H:%M:%S') - datetime.strptime(flights_used[0]['departure'], '%Y-%m-%dT%H:%M:%S')
            if flight['destination'] == destination \
                and (args.stops is None or (args.stops is not None and len(flights_used) - 1 <= args.stops)) \
                and (args.trip_duration is None or (args.trip_duration is not None and travel_time.total_seconds() / 3600 <= args.trip_duration)):
                combinations.append({
                    'flights': flights_used,
                    'bags_allowed': min([flight['bags_allowed'] for flight in flights_used]),
                    'bags_count': args.bags,
                    'destination': args.destination,
                    'origin': args.origin,
                    'total_price': sum([flight['base_price'] + flight['bag_price'] * args.bags for flight in flights_used]),
                    'travel_time': str(travel_time),
                    })
            else:
                next_minimum_accepted_departure = (datetime.strptime(flight['arrival'], '%Y-%m-%dT%H:%M:%S') + timedelta(hours=args.min_layover_time)).strftime('%Y-%m-%dT%H:%M:%S')
                next_maximum_accepted_departure = (datetime.strptime(flight['arrival'], '%Y-%m-%dT%H:%M:%S') + timedelta(hours=args.max_layover_time)).strftime('%Y-%m-%dT%H:%M:%S')
                recursive_search(clean_bad_flights(json.loads(json.dumps(data)),
                                                   airport_A=flight['origin'],
                                                   airport_B=flight['origin'],
                                                   departure_min=next_minimum_accepted_departure,
                                                   departure_max=next_maximum_accepted_departure),
                                 flight['destination'],
                                 destination,
                                 json.loads(json.dumps(flights_used)))
            flights_used = flights_used[:-1]


def build_round_trip_combinations(combinations_0, combinations_1) -> list:
    """ Build all possible combinations of round trips """
    combinations = []
    for combination_0 in combinations_0:
        for combination_1 in combinations_1:
            combination_0_arrival = datetime.strptime(combination_0['flights'][-1]['arrival'], '%Y-%m-%dT%H:%M:%S')
            combination_1_departure = datetime.strptime(combination_1['flights'][0]['departure'], '%Y-%m-%dT%H:%M:%S')
            if combination_1_departure >= combination_0_arrival + timedelta(hours=args.min_layover_time):
                combinations.append({
                    'flights': combination_0['flights'] + combination_1['flights'],
                    'bags_allowed': min([combination_0['bags_allowed'], combination_1['bags_allowed']]),
                    'bags_count': args.bags,
                    'destination': args.destination,
                    'origin': args.origin,
                    'total_price': combination_0['total_price'] + combination_1['total_price'],
                    'travel_time': str(max(timedelta_parse(combination_0['travel_time']), timedelta_parse(combination_1['travel_time']))),
                    })
    return sorted(combinations, key=lambda k: k['total_price'])


###
# Helper functions
###


def parse_ranges() -> None:
    """ Parse the ranges of dates and times """

    global outbound_range
    outbound_range = [None, None]
    if args.depart_day is not None:
        outbound_range = [args.depart_day + 'T00:00:00', args.depart_day + 'T23:59:59']
        if args.outbound_range is not None:
            outbound_range = [args.depart_day + 'T' + args.outbound_range.split('-')[0], args.depart_day + 'T' + args.outbound_range.split('-')[1]]
    elif args.outbound_range is not None:
        outbound_range = [args.outbound_range.split('-')[0], args.outbound_range.split('-')[1]]

    global return_range
    return_range = [None, None]
    if args.return_day is not None:
        return_range = [args.return_day + 'T00:00:00', args.return_day + 'T23:59:59']
        if args.return_range is not None:
            return_range = [args.return_day + 'T' + args.return_range.split('-')[0], args.return_day + 'T' + args.return_range.split('-')[1]]
    elif args.return_range is not None:
        return_range = [args.return_range.split('-')[0], args.return_range.split('-')[1]]


def read_csv_file(csv_file_path) -> list:
    """ Read csv file and return a json-compatible structured list of trips """
    with open(csv_file_path, 'r') as csv_file:
        reader = csv.DictReader(csv_file)
        return list(reader)


def timedelta_parse(string) -> timedelta:
    """ Parse a string in format [DD days, ]HH:MM:SS and return a timedelta object """
    h, m, s = string.split(':')
    if 'day' in h:
        h = int(h.split(' ')[0]) * 24 + int(h.split(' ')[-1])
    return timedelta(hours=int(h), minutes=int(m), seconds=int(s))


def print_combinations(combinations_found):
    """ Print the combinations found in a readable format """
    for combination in combinations_found:
        print('Total price: {}'.format(combination['total_price']))
        print('Travel time: {}'.format(combination['travel_time']))
        print('Bags allowed: {}'.format(combination['bags_allowed']))
        print('Bags count: {}'.format(combination['bags_count']))
        print('Flights:')
        for flight in combination['flights']:
            print('Flight from {} to {} at {} with {} bags arriving {}'.format(flight['origin'], flight['destination'], flight['departure'], flight['bags_allowed'], flight['arrival']))
        print('')


if __name__ == '__main__':
    main()


# error handling:
# - check all positional arguments are present and valid
# - check all optional arguments are valid
# - check csv file is valid

# - test ranges
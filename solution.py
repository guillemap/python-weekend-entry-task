import argparse
import json
import logging
from pprint import pprint
from datetime import datetime, timedelta
from helpers import *

logging.basicConfig(encoding="utf-8", level=logging.INFO)


def main():
    """Main function. Read the csv file, find the flights and print and/or store the results"""
    raw_data = read_csv_file(args.csv_file_path)
    if not args.round:
        results = find_flights(raw_data, args.origin, args.destination)
    else:
        results = build_round_trip_combinations(
            find_flights(raw_data, args.origin, args.destination),
            find_flights(raw_data, args.destination, args.origin, True),
        )
    if not args.not_print:
        pprint(results)
    if args.file:
        with open("results.json", "w") as f:
            json.dump(results, f, indent=4, sort_keys=True)


def find_flights(data, origin, destination, is_return=False) -> list:
    """Find all possible combinations of flights in data from origin to destination"""
    global combinations
    combinations = []
    filtered_data = clean_bad_flights(
        json.loads(json.dumps(data)),
        bags=args.bags,
        airport_A=destination,
        airport_B=origin,
        departure_min=return_range[0] if is_return else outbound_range[0],
        departure_max=return_range[1] if is_return else outbound_range[1],
        check_range=True,
    )
    recursive_search(filtered_data, origin, destination, [])
    return sorted(combinations, key=lambda k: k["total_price"])


def clean_bad_flights(
    data,
    bags=None,
    airport_A=None,
    airport_B=None,
    departure_min=None,
    departure_max=None,
    check_range=False,
) -> list:
    """
    Remove flights that fulfill any of the following conditions:
    a) allow less bags than the user has
    b) include the airport_A as origin or airport_B as destination
    c) have a departure time before the minimum accepted departure time
    d) have a departure time after the maximum accepted departure time
    e) we are checking an outbound/return range and the first flight is not in that range
    """
    for flight in json.loads(json.dumps(data)):
        if (
            (bags is not None and flight["bags_allowed"] < str(bags))
            or (airport_A is not None and airport_A == flight["origin"])
            or (airport_B is not None and airport_B == flight["destination"])
            or (
                not check_range
                and (
                    (departure_min is not None and flight["departure"] < departure_min)
                    or (
                        departure_max is not None
                        and flight["departure"] > departure_max
                    )
                )
            )
            or (
                check_range
                and airport_B == flight["origin"]
                and (
                    (
                        departure_min is not None
                        and is_full_timestamp(departure_min)
                        and flight["departure"] < departure_min
                    )
                    or (
                        departure_min is not None
                        and not is_full_timestamp(departure_min)
                        and flight["departure"][-8:] < departure_min
                    )
                    or (
                        departure_max is not None
                        and is_full_timestamp(departure_max)
                        and flight["departure"] > departure_max
                    )
                    or (
                        departure_max is not None
                        and not is_full_timestamp(departure_max)
                        and flight["departure"][-8:] > departure_max
                    )
                )
            )
        ):
            data.remove(flight)
    return data


def recursive_search(data, origin, destination, flights_used) -> None:
    """Recursive function to find all possible combinations of flights from origin to destination"""
    global combinations
    for flight in data:
        if flight["origin"] == origin:
            flight["base_price"] = float(flight["base_price"])
            flight["bag_price"] = float(flight["bag_price"])
            flight["bags_allowed"] = int(flight["bags_allowed"])
            flights_used.append(flight)
            travel_time = datetime.strptime(
                flight["arrival"], "%Y-%m-%dT%H:%M:%S"
            ) - datetime.strptime(flights_used[0]["departure"], "%Y-%m-%dT%H:%M:%S")
            if (
                flight["destination"] == destination
                and (
                    args.stops is None
                    or (args.stops is not None and len(flights_used) - 1 <= args.stops)
                )
                and (
                    args.trip_duration is None
                    or (
                        args.trip_duration is not None
                        and travel_time.total_seconds() / 3600 <= args.trip_duration
                    )
                )
            ):
                combinations.append(
                    {
                        "flights": flights_used,
                        "bags_allowed": min(
                            [flight["bags_allowed"] for flight in flights_used]
                        ),
                        "bags_count": args.bags,
                        "destination": args.destination,
                        "origin": args.origin,
                        "total_price": sum(
                            [
                                flight["base_price"] + flight["bag_price"] * args.bags
                                for flight in flights_used
                            ]
                        ),
                        "travel_time": str(travel_time),
                    }
                )
            else:
                next_minimum_accepted_departure = (
                    datetime.strptime(flight["arrival"], "%Y-%m-%dT%H:%M:%S")
                    + timedelta(hours=args.min_layover_time)
                ).strftime("%Y-%m-%dT%H:%M:%S")
                next_maximum_accepted_departure = (
                    datetime.strptime(flight["arrival"], "%Y-%m-%dT%H:%M:%S")
                    + timedelta(hours=args.max_layover_time)
                ).strftime("%Y-%m-%dT%H:%M:%S")
                recursive_search(
                    clean_bad_flights(
                        json.loads(json.dumps(data)),
                        airport_A=flight["origin"],
                        airport_B=flight["origin"],
                        departure_min=next_minimum_accepted_departure,
                        departure_max=next_maximum_accepted_departure,
                    ),
                    flight["destination"],
                    destination,
                    json.loads(json.dumps(flights_used)),
                )
            flights_used = flights_used[:-1]


def build_round_trip_combinations(combinations_0, combinations_1) -> list:
    """Build all possible combinations of round trips"""
    combinations = []
    for combination_0 in combinations_0:
        for combination_1 in combinations_1:
            combination_0_arrival = datetime.strptime(
                combination_0["flights"][-1]["arrival"], "%Y-%m-%dT%H:%M:%S"
            )
            combination_1_departure = datetime.strptime(
                combination_1["flights"][0]["departure"], "%Y-%m-%dT%H:%M:%S"
            )
            if combination_1_departure >= combination_0_arrival + timedelta(
                hours=args.min_layover_time
            ):
                combinations.append(
                    {
                        "flights": combination_0["flights"] + combination_1["flights"],
                        "bags_allowed": min(
                            [
                                combination_0["bags_allowed"],
                                combination_1["bags_allowed"],
                            ]
                        ),
                        "bags_count": args.bags,
                        "destination": args.destination,
                        "origin": args.origin,
                        "total_price": combination_0["total_price"]
                        + combination_1["total_price"],
                        "travel_time": str(
                            max(
                                timedelta_parse(combination_0["travel_time"]),
                                timedelta_parse(combination_1["travel_time"]),
                            )
                        ),
                    }
                )
    return sorted(combinations, key=lambda k: k["total_price"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Python weekend entry task")
    parser.add_argument(
        "csv_file_path", help="Relative path of the csv dataset file", type=str
    )
    parser.add_argument("origin", help="Airport A", type=str)
    parser.add_argument("destination", help="Airport B", type=str)
    parser.add_argument(
        "-b",
        "--bags",
        help="Number of bags. If not specified, it is assumed that the user has no bags.",
        type=int,
        default=0,
    )
    parser.add_argument(
        "-R",
        "--return",
        dest="round",
        help="If the user returns back to origin.",
        action="store_true",
    )
    parser.add_argument(
        "-l",
        "--min-layover-time",
        help="Minimum layover hours accepted.",
        type=int,
        default=1,
    )
    parser.add_argument(
        "-L",
        "--max-layover-time",
        help="Maximum layover hours accepted.",
        type=int,
        default=6,
    )
    parser.add_argument(
        "-d",
        "--depart-day",
        help="Day to start flyign to destination in format YYYY-MM-DD.",
        type=str,
    )
    parser.add_argument(
        "-r",
        "--return-day",
        help="Day to start flyign back to origin in format YYYY-MM-DD, if there is a return trip.",
        type=str,
    )
    parser.add_argument("-s", "--stops", help="Maximum number of stops.", type=int)
    parser.add_argument(
        "-or",
        "--outbound-range",
        help="Time range of accepted outbound departure flight times in format HH:MM:SS-HH:MM:SS.",
        type=str,
    )
    parser.add_argument(
        "-rr",
        "--return-range",
        help="Time range of accepted return departure flight times in format HH:MM:SS-HH:MM:SS.",
        type=str,
    )
    parser.add_argument(
        "-t",
        "--trip-duration",
        help="Maximum trip duration in hours (A -> B). For round trips it is the maximum time of any of both trips, using Skyscanner's standard.",
        type=float,
    )
    parser.add_argument(
        "-f", "--file", help="Save results to file results.json.", action="store_true"
    )
    parser.add_argument(
        "-n",
        "--not-print",
        help="Avoid printing the combinations found",
        action="store_true",
    )
    args = parser.parse_args()
    check_input_arguments(args)
    outbound_range, return_range = parse_ranges(args)
    main()

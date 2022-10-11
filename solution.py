import argparse
import json
import logging
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
        print(json.dumps(results, indent=4))
    if args.file:
        with open("results.json", "w") as f:
            json.dump(results, f, indent=4)


def find_flights(data, origin, destination, is_return=False) -> list:
    """Find all possible combinations of flights in data from origin to destination"""
    global combinations
    combinations = []
    filtered_data = clean_flights_from(data, destination)
    filtered_data = clean_flights_to(filtered_data, origin)
    timestamp_range = outbound_range if not is_return else return_range
    filtered_data = clean_flights_from_airport_departing_outside_range(
        filtered_data, origin, timestamp_range[0], timestamp_range[1]
    )
    recursive_search(filtered_data, origin, destination, [])
    return sorted(combinations, key=lambda k: k["total_price"])


def clean_flights_from(data, airport):
    """Remove all flights from data that depart from airport"""
    return [flight for flight in data if flight["origin"] != airport]


def clean_flights_to(data, airport):
    """Remove all flights from data that arrive to airport"""
    return [flight for flight in data if flight["destination"] != airport]


def clean_flights_departing_before(data, departure_before):
    """Remove all flights from data that depart before departure_before"""
    return [flight for flight in data if flight["departure"] >= departure_before]


def clean_flights_from_airport_departing_outside_range(
    data, airport, departure_before, departure_after
):
    """Remove all flights from data that depart from airport and that depart before departure_before or after departure_after"""
    new_data = json.loads(json.dumps(data))
    for flight in data:
        if flight["origin"] == airport:
            deapart_hh_mm_ss = flight["departure"].split("T")[1]
            if (
                departure_before is not None
                and (
                    (
                        is_full_timestamp(departure_before)
                        and flight["departure"] < departure_before
                    )
                    or (
                        not is_full_timestamp(departure_before)
                        and deapart_hh_mm_ss < departure_before
                    )
                )
            ) or (
                departure_after is not None
                and (
                    (
                        is_full_timestamp(departure_after)
                        and flight["departure"] > departure_after
                    )
                    or (
                        not is_full_timestamp(departure_after)
                        and deapart_hh_mm_ss > departure_after
                    )
                )
            ):
                new_data.remove(flight)
    return new_data


def recursive_search(data, origin, destination, flights_used) -> None:
    """Recursive function to find all possible combinations of flights from origin to destination"""
    global combinations
    for flight in data:
        if flight["origin"] == origin:
            flight["base_price"] = float(flight["base_price"])
            flight["bag_price"] = float(flight["bag_price"])
            flight["bags_allowed"] = int(flight["bags_allowed"])
            flights_used.append(flight)
            travel_time = datetime.fromisoformat(
                flight["arrival"]
            ) - datetime.fromisoformat(flights_used[0]["departure"])
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
                    datetime.fromisoformat(flight["arrival"])
                    + timedelta(hours=args.min_layover_time)
                ).isoformat()
                next_maximum_accepted_departure = (
                    datetime.fromisoformat(flight["arrival"])
                    + timedelta(hours=args.max_layover_time)
                ).isoformat()
                temp_data = clean_flights_from(data, flight["origin"])
                temp_data = clean_flights_to(temp_data, flight["destination"])
                temp_data = clean_flights_departing_before(
                    temp_data, next_minimum_accepted_departure
                )
                temp_data = clean_flights_from_airport_departing_outside_range(
                    temp_data,
                    flight["destination"],
                    next_minimum_accepted_departure,
                    next_maximum_accepted_departure,
                )
                recursive_search(
                    temp_data,
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
            combination_0_arrival = datetime.fromisoformat(
                combination_0["flights"][-1]["arrival"]
            )
            combination_1_departure = datetime.fromisoformat(
                combination_1["flights"][0]["departure"]
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

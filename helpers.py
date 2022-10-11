import logging
import os
import csv
import re
from datetime import timedelta

logger = logging.getLogger(__name__)


def parse_ranges(args) -> None:
    """Parse the ranges of dates and times"""
    outbound_range = [None, None]
    if args.depart_day is not None:
        outbound_range = [args.depart_day + "T00:00:00", args.depart_day + "T23:59:59"]
        if args.outbound_range is not None:
            outbound_range = [
                args.depart_day + "T" + args.outbound_range.split("-")[0],
                args.depart_day + "T" + args.outbound_range.split("-")[1],
            ]
    elif args.outbound_range is not None:
        outbound_range = [
            args.outbound_range.split("-")[0],
            args.outbound_range.split("-")[1],
        ]
    return_range = [None, None]
    if args.return_day is not None:
        return_range = [args.return_day + "T00:00:00", args.return_day + "T23:59:59"]
        if args.return_range is not None:
            return_range = [
                args.return_day + "T" + args.return_range.split("-")[0],
                args.return_day + "T" + args.return_range.split("-")[1],
            ]
    elif args.return_range is not None:
        return_range = [
            args.return_range.split("-")[0],
            args.return_range.split("-")[1],
        ]
    return outbound_range, return_range


def read_csv_file(csv_file_path) -> list:
    """Read csv file and return a json-compatible structured list of trips"""
    if not os.path.exists(csv_file_path):
        logger.error("File {} does not exist".format(csv_file_path))
        exit(1)
    with open(csv_file_path, "r") as csv_file:
        reader = csv.DictReader(csv_file)
        if (
            "flight_no" not in reader.fieldnames
            or "origin" not in reader.fieldnames
            or "destination" not in reader.fieldnames
            or "departure" not in reader.fieldnames
            or "arrival" not in reader.fieldnames
            or "base_price" not in reader.fieldnames
            or "bag_price" not in reader.fieldnames
            or "bags_allowed" not in reader.fieldnames
        ):
            logger.error(
                "The csv file must contain the following fields: flight_no, origin, destination, departure, arrival, base_price, bag_price, bags_allowed"
            )
            exit(1)
        return [f for f in reader if flight_is_valid(f)]


def timedelta_parse(string) -> timedelta:
    """Parse a string in format [DD days, ]HH:MM:SS and return a timedelta object"""
    h, m, s = string.split(":")
    if "day" in h:
        h = int(h.split(" ")[0]) * 24 + int(h.split(" ")[-1])
    return timedelta(hours=int(h), minutes=int(m), seconds=int(s))


def is_full_timestamp(timestamp) -> bool:
    """Check if a timestamp is in full format (YYYY-MM-DDTHH:MM:SS)"""
    return re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", timestamp)


def check_input_arguments(args) -> None:
    """Check if the input arguments are valid"""
    if args.bags is not None and args.bags < 0:
        logger.error("--bags must be a positive integer")
        exit(1)
    if args.min_layover_time is not None and args.min_layover_time < 0:
        logger.error("--min-layover-time must be a positive integer")
        exit(1)
    if args.max_layover_time is not None and args.max_layover_time < 0:
        logger.error("--max-layover-time must be a positive integer")
        exit(1)
    if args.depart_day is not None and not re.match(
        r"^\d{4}-\d{2}-\d{2}$", args.depart_day
    ):
        logger.error("--depart-day must be in format YYYY-MM-DD")
        exit(1)
    if args.return_day is not None and not re.match(
        r"^\d{4}-\d{2}-\d{2}$", args.return_day
    ):
        logger.error("--return-day must be in format YYYY-MM-DD")
        exit(1)
    if args.stops is not None and args.stops < 0:
        logger.error("--stops must be a positive integer")
        exit(1)
    if args.outbound_range is not None and not re.match(
        r"^\d{2}:\d{2}:\d{2}-\d{2}:\d{2}:\d{2}$", args.outbound_range
    ):
        logger.error("--outbound-range must be in format HH:MM:SS-HH:MM:SS")
        exit(1)
    if args.return_range is not None and not re.match(
        r"^\d{2}:\d{2}:\d{2}-\d{2}:\d{2}:\d{2}$", args.return_range
    ):
        logger.error("--return-range must be in format HH:MM:SS-HH:MM:SS")
        exit(1)
    if args.trip_duration is not None and args.trip_duration < 0:
        logger.error("--trip-duration must be a positive integer")
        exit(1)


def flight_is_valid(flight) -> bool:
    """Check if a flight is valid"""
    if flight["origin"] == flight["destination"]:
        logger.info(
            "Flight {} departing at {} is invalid because origin and destination are the same".format(
                flight["flight_no"], flight["departure"]
            )
        )
        return False
    if not re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", flight["departure"]):
        logger.info(
            "Flight {} departing at {} is invalid because departure is not in format YYYY-MM-DDTHH:MM:SS".format(
                flight["flight_no"], flight["departure"]
            )
        )
        return False
    if not re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", flight["arrival"]):
        logger.info(
            "Flight {} departing at {} is invalid because arrival is not in format YYYY-MM-DDTHH:MM:SS".format(
                flight["flight_no"], flight["arrival"]
            )
        )
        return False
    if flight["departure"] > flight["arrival"]:
        logger.info(
            "Flight {} departing at {} is invalid because arrival is before departure".format(
                flight["flight_no"], flight["departure"]
            )
        )
        return False
    try:
        float(flight["base_price"])
    except ValueError:
        logger.info(
            "Flight {} departing at {} is invalid because base_price is not a number".format(
                flight["flight_no"], flight["departure"]
            )
        )
        return False
    try:
        float(flight["bag_price"])
    except ValueError:
        logger.info(
            "Flight {} departing at {} is invalid because bag_price is not a number".format(
                flight["flight_no"], flight["departure"]
            )
        )
        return False
    try:
        int(flight["bags_allowed"])
    except ValueError:
        logger.info(
            "Flight {} departing at {} is invalid because bags_allowed is not an integer".format(
                flight["flight_no"], flight["departure"]
            )
        )
        return False
    if float(flight["base_price"]) < 0:
        logger.info(
            "Flight {} departing at {} is invalid because base_price is negative".format(
                flight["flight_no"], flight["departure"]
            )
        )
        return False
    if float(flight["bag_price"]) < 0:
        logger.info(
            "Flight {} departing at {} is invalid because bag_price is negative".format(
                flight["flight_no"], flight["departure"]
            )
        )
        return False
    if int(flight["bags_allowed"]) < 0:
        logger.info(
            "Flight {} departing at {} is invalid because bags_allowed is negative".format(
                flight["flight_no"], flight["departure"]
            )
        )
        return False
    return True


############################################
# Debugging
############################################


def flight_to_str(flight, fail_reason=[]) -> None:
    """flight in a human-readable format"""
    return "Flight No.: {} - {} -> {} - Departure: {} - Arrival: {} - Base Price: {} - Bag Price: {} - Bags Allowed: {}".format(
        (colors.FAIL if "flight_no" in fail_reason else "")
        + flight["flight_no"]
        + colors.ENDC,
        (colors.FAIL if "origin" in fail_reason else "")
        + flight["origin"]
        + colors.ENDC,
        (colors.FAIL if "destination" in fail_reason else "")
        + flight["destination"]
        + colors.ENDC,
        (colors.FAIL if "departure" in fail_reason else "")
        + flight["departure"]
        + colors.ENDC,
        (colors.FAIL if "arrival" in fail_reason else "")
        + flight["arrival"]
        + colors.ENDC,
        (colors.FAIL if "base_price" in fail_reason else "")
        + str(flight["base_price"])
        + colors.ENDC,
        (colors.FAIL if "bag_price" in fail_reason else "")
        + str(flight["bag_price"])
        + colors.ENDC,
        (colors.FAIL if "bags_allowed" in fail_reason else "")
        + str(flight["bags_allowed"])
        + colors.ENDC,
    )


def print_data_csv(data) -> None:
    """Print the data in a csv format"""
    for flight in data:
        print(
            "{},{},{},{},{},{},{},{}".format(
                flight["flight_no"],
                flight["origin"],
                flight["destination"],
                flight["departure"],
                flight["arrival"],
                flight["base_price"],
                flight["bag_price"],
                flight["bags_allowed"],
            )
        )


def print_combination_found(combination) -> None:
    """Print a combination of flights in a human-readable format"""
    print("Combination found:")
    for flight in combination["flights"]:
        print(flight_to_str(flight))
    print("")


class colors:
    """Colors for the terminal"""

    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"

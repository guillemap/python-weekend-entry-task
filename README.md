# Python weekend entry task

Script that fulfills all official readme requirements. In addition it includes some extra filters which are popular on flight search websites like Skyscanner.

To run the script simply run the command

```
python -m solution example/example0.csv RFZ WIW
```

As expected it will print the result in the terminal itself as a formatted json. A file can be stored in the same directory as the script, using as well an extra optional argument.

```
positional arguments:
  csv_file_path         Relative path of the csv dataset file
  origin                Airport A
  destination           Airport B

options:
  -h, --help            show this help message and exit
  -b BAGS, --bags BAGS  Number of bags. If not specified, it is assumed that the user has no
                        bags.
  -R, --return          If the user returns back to origin.
  -l MIN_LAYOVER_TIME, --min-layover-time MIN_LAYOVER_TIME
                        Minimum layover hours accepted.
  -L MAX_LAYOVER_TIME, --max-layover-time MAX_LAYOVER_TIME
                        Maximum layover hours accepted.
  -d DEPART_DAY, --depart-day DEPART_DAY
                        Day to start flyign to destination in format YYYY-MM-DD.
  -r RETURN_DAY, --return-day RETURN_DAY
                        Day to start flyign back to origin in format YYYY-MM-DD, if there is a
                        return trip.
  -s STOPS, --stops STOPS
                        Maximum number of stops.
  -or OUTBOUND_RANGE, --outbound-range OUTBOUND_RANGE
                        Time range of accepted outbound departure flight times in format
                        HH:MM:SS-HH:MM:SS.
  -rr RETURN_RANGE, --return-range RETURN_RANGE
                        Time range of accepted return departure flight times in format HH:MM:SS-
                        HH:MM:SS.
  -t TRIP_DURATION, --trip-duration TRIP_DURATION
                        Maximum trip duration in hours (A -> B). For round trips it is the
                        maximum time of any of both trips, using Skyscanner's standard.
  -f, --file            Save results to file results.json.
```

#### Assumptions:

1. bags_allowed is an integer
2. departure/arrival are in the format of YYYY-MM-DDTHH:MM:SS
3. travel_time for round trips is the maximum time of both trips, using SkyScanner's standard

---

## Python weekend entry task official readme:

**Write a python script/module/package, that for a given flight data in a form of `csv` file (check the examples), prints out a structured list of all flight combinations for a selected route between airports A -> B, sorted by the final price for the trip.**

### Description

You've been provided with some semi-randomly generated example csv datasets you can use to test your solution. The datasets have following columns:

- `flight_no`: Flight number.
- `origin`, `destination`: Airport codes.
- `departure`, `arrival`: Dates and times of the departures/arrivals.
- `base_price`, `bag_price`: Prices of the ticket and one piece of baggage.
- `bags_allowed`: Number of allowed pieces of baggage for the flight.

In addition to the dataset, your script will take some additional arguments as input:

| Argument name | type   | Description              | Notes |
| ------------- | ------ | ------------------------ | ----- |
| `origin`      | string | Origin airport code      |       |
| `destination` | string | Destination airport code |       |

### Search restrictions

- By default you're performing search on ALL available combinations, according to search parameters.
- In case of a combination of A -> B -> C, the layover time in B should **not be less than 1 hour and more than 6 hours**.
- No repeating airports in the same trip!
  - A -> B -> A -> C is not a valid combination for search A -> C.
- Output is sorted by the final price of the trip.

#### Optional arguments

You may add any number of additional search parameters to boost your chances to attend. Here are 2 recommended ones:

| Argument name | type    | Description              | Notes                        |
| ------------- | ------- | ------------------------ | ---------------------------- |
| `bags`        | integer | Number of requested bags | Optional (defaults to 0)     |
| `return`      | boolean | Is it a return flight?   | Optional (defaults to false) |

##### Performing return trip search

Example input (assuming `solution.py` is the main module):

```
python -m solution example/example0.csv RFZ WIW --bags=1 --return
```

will perform a search RFZ -> WIW -> RFZ for flights which allow at least 1 piece of baggage.

- **NOTE:** Since WIW is in this case the final destination for one part of the trip, the layover rule does not apply.

#### Output

The output will be a json-compatible structured list of trips sorted by price. The trip has the following schema:
| Field | Description |
|----------------|---------------------------------------------------------------|
| `flights` | A list of flights in the trip according to the input dataset. |
| `origin` | Origin airport of the trip. |
| `destination` | The final destination of the trip. |
| `bags_allowed` | The number of allowed bags for the trip. |
| `bags_count` | The searched number of bags. |
| `total_price` | The total price for the trip. |
| `travel_time` | The total travel time. |

**For more information, check the example section.**

### Points of interest

Assuming your solution is working, we'll be additionally judging based on following skills:

- input, output - what if we input garbage?
- modules, packages & code structure (hint: it's easy to overdo it)
- usage of standard library and built-in data structures
- code readability, clarity, used conventions, documentation and comments

## Requirements and restrictions

- **Your solution needs to contain a README file describing what it does and how to run it.**
- Only the standard library is allowed, no 3rd party packages, notebooks, specialized distros (Conda) etc.
- The code should run as is, no environment setup should be required.

## Submissions

Follow the instructions you received in the email.

## Example behaviour

Let's imagine we wrote our solution into one file, `solution.py` and our datatset is in `data.csv`.
We want to test the script by performing a flight search on route BTW -> REJ (we know the airports are present in the dataset) with one bag. We run the thing:

```bash
python -m solution data.csv BTW REJ --bags=1
```

and get the following result:

```json
[
  {
    "flights": [
      {
        "flight_no": "XC233",
        "origin": "BTW",
        "destination": "WTF",
        "departure": "2021-09-02T05:50:00",
        "arrival": "2021-09-02T8:20:00",
        "base_price": 67.0,
        "bag_price": 7.0,
        "bags_allowed": 2
      },
      {
        "flight_no": "VJ832",
        "origin": "WTF",
        "destination": "REJ",
        "departure": "2021-09-02T11:05:00",
        "arrival": "2021-09-02T12:45:00",
        "base_price": 31.0,
        "bag_price": 5.0,
        "bags_allowed": 1
      }
    ],
    "bags_allowed": 1,
    "bags_count": 1,
    "destination": "REJ",
    "origin": "BTW",
    "total_price": 110.0,
    "travel_time": "6:55:00"
  },
  {
    "flights": [
      {
        "flight_no": "JV042",
        "origin": "BTW",
        "destination": "REJ",
        "departure": "2021-09-01T17:35:00",
        "arrival": "2021-09-01T21:05:00",
        "base_price": 216.0,
        "bag_price": 11.0,
        "bags_allowed": 2
      }
    ],
    "bags_allowed": 2,
    "bags_count": 1,
    "destination": "REJ",
    "origin": "BTW",
    "total_price": 227.0,
    "travel_time": "3:30:00"
  }
]
```

import os
import pandas as pd
import requests
import random
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Ensure the script uses its own directory as the working directory
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# Define paths to your data
data_dir = '../data/outputs/csv/'  # Update with your actual relative path

# Load the addresses
origin_addresses = pd.read_csv(os.path.join(data_dir, 'top_origin_addresses.csv'))
destination_addresses = pd.read_csv(os.path.join(data_dir, 'top_destination_addresses.csv'))

logging.debug(f"Loaded {len(origin_addresses)} origin addresses and {len(destination_addresses)} destination addresses.")

# Function to generate a random time within the commuting windows
def get_random_commute_time():
    morning_window_start = datetime.now().replace(hour=6, minute=30, second=0, microsecond=0)
    morning_window_end = morning_window_start.replace(hour=9, minute=0)
    evening_window_start = datetime.now().replace(hour=16, minute=0, second=0, microsecond=0)
    evening_window_end = evening_window_start.replace(hour=18, minute=30)

    if random.choice(['morning', 'evening']) == 'morning':
        commute_time = morning_window_start + timedelta(
            minutes=random.randint(0, int((morning_window_end - morning_window_start).total_seconds() // 60))
        )
        return 'morning', commute_time
    else:
        commute_time = evening_window_start + timedelta(
            minutes=random.randint(0, int((evening_window_end - evening_window_start).total_seconds() // 60))
        )
        return 'evening', commute_time

# Function to generate a route using OTP for a specific mode
def generate_route(origin, destination, departure_time, mode):
    url = "http://localhost:8080/otp/routers/default/plan"
    params = {
        'fromPlace': f"{origin['Latitude']},{origin['Longitude']}",
        'toPlace': f"{destination['Latitude']},{destination['Longitude']}",
        'mode': mode,
        'date': departure_time.strftime('%Y-%m-%d'),
        'time': departure_time.strftime('%H:%M:%S'),
        'arriveBy': 'false',
        'maxWalkDistance': '1500',
        'wheelchair': 'false',
        'locale': 'en',
    }
    logging.debug(f"Sending OTP request for {mode} from {origin['Address']} to {destination['Address']} at {departure_time}")
    response = requests.get(url, params=params)
    if response.status_code == 200:
        logging.debug(f"Route successfully retrieved for {mode} from {origin['Address']} to {destination['Address']}")
        return response.json()
    else:
        logging.error(f"Error in request: {response.status_code}, {response.text}")
        return None

# Function to process and summarize the route details
def process_route(route, mode):
    if route is None or 'plan' not in route or 'itineraries' not in route['plan'] or not route['plan']['itineraries']:
        logging.warning(f"No route found for mode {mode}.")
        return None

    itinerary = route['plan']['itineraries'][0]
    total_km = 0
    total_duration_min = 0
    transit_details = []
    all_legs = []
    route_shape = ''

    for leg in itinerary['legs']:
        distance_km = leg['distance'] / 1000  # Convert to km
        duration_min = leg['duration'] / 60  # Convert to minutes
        total_km += distance_km
        total_duration_min += duration_min
        leg_geometry = leg.get('legGeometry', {}).get('points', '')
        if leg_geometry:
            if not route_shape:
                route_shape = leg_geometry
            else:
                route_shape += leg_geometry
        leg_info = {
            'mode': leg['mode'],
            'distance_km': distance_km,
            'duration_min': duration_min,
            'from_place': leg['from']['name'],
            'to_place': leg['to']['name'],
            'leg_geometry': leg_geometry
        }
        logging.debug(f"Processed leg: {leg_info}")
        if leg['mode'] in ['BUS', 'RAIL', 'TRAM', 'SUBWAY', 'FERRY']:
            leg_info.update({
                'agency_name': leg.get('agencyName'),
                'agency_id': leg.get('agencyId'),
                'route': leg.get('route'),
                'route_name': leg.get('routeLongName'),
                'from_station': leg['from'].get('stopId'),
                'to_station': leg['to'].get('stopId')
            })
            transit_details.append(leg_info)
        all_legs.append(leg_info)

    return {
        'mode': mode,
        'total_km': total_km,
        'total_duration_min': total_duration_min,
        'transit_details': transit_details,
        'all_legs': all_legs,
        'route_shape': route_shape
    }

# Function to get valid O/D pairs
def get_valid_pairs(origins, destinations):
    valid_pairs = [
        (origin, destination)
        for _, origin in origins.iterrows()
        for _, destination in destinations.iterrows()
    ]
    logging.debug(f"Generated {len(valid_pairs)} valid origin-destination pairs.")
    return valid_pairs

# Main function
def main():
    valid_pairs = get_valid_pairs(origin_addresses, destination_addresses)
    num_od_pairs = 10000
    num_samples = min(num_od_pairs, len(valid_pairs))
    if num_samples == 0:
        logging.error("No valid origin-destination pairs found.")
        return

    selected_pairs = random.sample(valid_pairs, num_samples)
    route_summaries = []
    modes = ['BICYCLE', 'CAR', 'TRANSIT']

    for origin, destination in selected_pairs:
        time_of_day, departure_time = get_random_commute_time()
        dist = ((origin['Latitude'] - destination['Latitude'])**2 + (origin['Longitude'] - destination['Longitude'])**2)**0.5 * 111  # Approximate km distance

        for mode in modes:
            if mode == 'BICYCLE' and dist > 30:
                logging.info(f"Skipping long-distance BICYCLE route from {origin['Address']} to {destination['Address']}")
                continue

            logging.info(f"Generating {mode} route from {origin['Address']} to {destination['Address']} at {departure_time}")
            route_info = generate_route(origin, destination, departure_time, mode)
            route_summary = process_route(route_info, mode)

            if route_summary:
                logging.debug(f"Processed route summary for {mode} from {origin['Address']} to {destination['Address']}")
                summary = {
                    'origin_address': origin['Address'],
                    'destination_address': destination['Address'],
                    'origin_latitude': origin['Latitude'],
                    'origin_longitude': origin['Longitude'],
                    'destination_latitude': destination['Latitude'],
                    'destination_longitude': destination['Longitude'],
                    'departure_time': departure_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'time_of_day': time_of_day,
                    'mode': route_summary['mode'],
                    'total_km': route_summary['total_km'],
                    'total_duration_min': route_summary['total_duration_min'],
                    'transit_details': route_summary['transit_details'],
                    'all_legs': route_summary['all_legs'],
                    'route_shape': route_summary['route_shape']
                }
                route_summaries.append(summary)
            else:
                logging.warning(f"Route for {mode} from {origin['Address']} to {destination['Address']} could not be processed.")

    df_summary = pd.DataFrame(route_summaries)
    output_summary_file = os.path.join(data_dir, 'route_summary_with_commute_times.csv')
    df_summary.to_csv(output_summary_file, index=False)
    logging.info(f"Route summary with commute times saved to '{output_summary_file}'")

if __name__ == "__main__":
    main()
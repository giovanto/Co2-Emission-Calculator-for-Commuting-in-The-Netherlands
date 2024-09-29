import os
import pandas as pd
import ast  # To safely evaluate string representations of lists
import logging  # To add debug logs
import polyline  # To decode polyline for mapping
from shapely.geometry import LineString
import json  # To handle GeoJSON
from geojson import Feature, FeatureCollection, LineString as GeoJSONLineString

# Ensure the script uses its own directory as the working directory
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# Setup logging for debugging
logging.basicConfig(level=logging.DEBUG, filename='co2_calculator_debug.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')

# WPM TTW CO2 emission factors
WPM_TTW_CO2_FACTORS = {
    'CAR': 138.67,
    'BICYCLE': 0.0,
    'TRANSIT': 15
}

# WTW CO2 emission factors
WTW_CO2_FACTORS = {
    'CAR': 193,
    'BICYCLE': 3,
    'TRANSIT': 20
}

# Function to classify commute distance groups
def classify_commute_distance(distance_km):
    if distance_km < 10:
        return "short"
    elif 10 <= distance_km <= 30:
        return "medium"
    else:
        return "long"

# CO2 Emission Calculations for Method 1 (WPM TTW) and Method 2 (WTW)
def calculate_co2_emissions_method_1(mode, distance_km):
    if mode.upper() in ['TRANSIT', 'BUS', 'TRAM', 'RAIL', 'SUBWAY', 'FERRY']:
        mode = 'TRANSIT'
    return distance_km * WPM_TTW_CO2_FACTORS.get(mode.upper(), 0.0)

def calculate_co2_emissions_method_2(mode, distance_km):
    if mode.upper() in ['TRANSIT', 'BUS', 'TRAM', 'RAIL', 'SUBWAY', 'FERRY']:
        mode = 'TRANSIT'
    return distance_km * WTW_CO2_FACTORS.get(mode.upper(), 0.0)

# Function to decode polyline for GeoJSON with reversed coordinates (Lat, Lon -> Lon, Lat)
def polyline_to_geojson(encoded_shape):
    try:
        decoded_shape = polyline.decode(encoded_shape)
        if decoded_shape:
            # Reverse the order of coordinates from (lat, lon) to (lon, lat)
            reversed_shape = [(lon, lat) for lat, lon in decoded_shape]
            return GeoJSONLineString(reversed_shape)
        return None
    except Exception as e:
        logging.error(f"Error decoding polyline to GeoJSON: {e}")
        return None

# Function to decode polyline to WKT
def polyline_to_wkt(encoded_shape):
    try:
        decoded_shape = polyline.decode(encoded_shape)
        if decoded_shape:
            reversed_shape = [(lon, lat) for lat, lon in decoded_shape]
            line = LineString(reversed_shape)
            return line.wkt
        return None
    except Exception as e:
        logging.error(f"Error decoding polyline to WKT: {e}")
        return None

# Process input and create both CSV and GeoJSON output
def process_trip_legs_for_qgis(input_file, output_file_csv, output_file_geojson):
    try:
        # Read the CSV file
        df = pd.read_csv(input_file)
        logging.info(f"Loaded {len(df)} rows from {input_file}")
    except Exception as e:
        logging.error(f"Failed to load input file: {e}")
        return

    # List to hold simplified CSV data
    simplified_data = []
    
    # List to hold GeoJSON features
    geojson_features = []

    # Iterate through each trip row in the dataframe
    for index, row in df.iterrows():
        try:
            trip_id = index + 1  # Create a unique trip ID
            origin_address = row['origin_address']
            destination_address = row['destination_address']
            origin_lat = row['origin_latitude']
            origin_lon = row['origin_longitude']
            destination_lat = row['destination_latitude']
            destination_lon = row['destination_longitude']

            # Safely evaluate the 'all_legs' field (convert string to list)
            legs = ast.literal_eval(row['all_legs'])

            # Iterate through each leg of the trip
            total_co2_method_1 = 0
            total_co2_method_2 = 0
            legs_details = []

            for leg_index, leg in enumerate(legs):
                mode = leg['mode']
                distance_km = leg['distance_km']
                duration_min = leg.get('duration_min', 0)

                # Calculate CO2 emissions for both methods
                co2_method_1 = calculate_co2_emissions_method_1(mode, distance_km)
                co2_method_2 = calculate_co2_emissions_method_2(mode, distance_km)
                total_co2_method_1 += co2_method_1
                total_co2_method_2 += co2_method_2

                # Decode leg geometry to GeoJSON and WKT
                leg_geometry_geojson = polyline_to_geojson(leg.get('leg_geometry', ''))
                leg_geometry_wkt = polyline_to_wkt(leg.get('leg_geometry', ''))

                # Append leg details for CSV output
                legs_details.append({
                    'trip_id': trip_id,
                    'leg_id': f"{trip_id}_{leg_index+1}",  # Unique leg ID within the trip
                    'mode': mode,
                    'distance_km': distance_km,
                    'duration_min': duration_min,
                    'co2_emissions_method_1_g': co2_method_1,  # CO2 in grams (Method 1)
                    'co2_emissions_method_2_g': co2_method_2,  # CO2 in grams (Method 2),
                    'leg_geometry_wkt': leg_geometry_wkt
                })

                # Add the leg as a GeoJSON feature
                if leg_geometry_geojson:
                    feature = Feature(geometry=leg_geometry_geojson, properties={
                        'trip_id': trip_id,
                        'leg_id': f"{trip_id}_{leg_index+1}",  # Unique leg ID within the trip
                        'mode': mode,
                        'distance_km': distance_km,
                        'duration_min': duration_min,
                        'co2_emissions_method_1_g': co2_method_1,
                        'co2_emissions_method_2_g': co2_method_2,
                        'origin_address': origin_address,
                        'destination_address': destination_address,
                        'origin_lat': origin_lat,
                        'origin_lon': origin_lon,
                        'destination_lat': destination_lat,
                        'destination_lon': destination_lon
                    })
                    geojson_features.append(feature)

            # Add the simplified row data for the entire trip (CSV)
            simplified_data.append({
                'trip_id': trip_id,
                'origin_address': origin_address,
                'destination_address': destination_address,
                'origin_lat': origin_lat,
                'origin_lon': origin_lon,
                'destination_lat': destination_lat,
                'destination_lon': destination_lon,
                'total_km': row['total_km'],
                'mode': row['mode'],
                'total_duration_min': row['total_duration_min'],
                'total_co2_emissions_method_1_g': total_co2_method_1,
                'total_co2_emissions_method_2_g': total_co2_method_2,
                'commute_distance_group': classify_commute_distance(row['total_km']),
                'legs': legs_details  # Include detailed legs
            })

        except Exception as e:
            logging.error(f"Error processing trip {index + 1}: {e}")

    # Create a DataFrame from the simplified data for CSV
    simplified_df = pd.DataFrame(simplified_data)
    
    # Write the simplified CSV file
    simplified_df.to_csv(output_file_csv, index=False)
    logging.info(f"Simplified data saved to {output_file_csv}")
    print(f"Simplified data saved to {output_file_csv}")

    # Create a GeoJSON FeatureCollection and save it
    geojson_feature_collection = FeatureCollection(geojson_features)
    with open(output_file_geojson, 'w') as geojson_file:
        json.dump(geojson_feature_collection, geojson_file, indent=4)
    logging.info(f"GeoJSON data saved to {output_file_geojson}")
    print(f"GeoJSON data saved to {output_file_geojson}")

# Example usage
input_file = '../data/outputs/csv/route_summary_with_commute_times.csv'
output_file_csv = '../data/outputs/csv/co2_emissions_summary.csv'
output_file_geojson = '../data/outputs/csv/co2_emissions_summary.geojson'

process_trip_legs_for_qgis(input_file, output_file_csv, output_file_geojson)

process_trip_legs_for_qgis(input_file, output_file_csv, output_file_geojson)
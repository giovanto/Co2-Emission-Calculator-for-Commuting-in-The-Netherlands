import os
import pandas as pd
import json
from shapely.geometry import shape, Point
import random
import requests
import logging

# Setup logging for debugging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Ensure the script uses its own directory as the working directory
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# Define the paths to the input and output datasets
data_dir = '../data/'
processed_data_dir = os.path.join(data_dir, 'processed/')
output_dir = os.path.join(data_dir, 'outputs/csv/')

georef_file_path = os.path.join(processed_data_dir, 'cleaned_georef-netherlands-postcode-pc4.csv')
top_origin_zipcodes_path = os.path.join(processed_data_dir, 'top_origin_zipcodes.csv')
top_destination_zipcodes_path = os.path.join(processed_data_dir, 'top_destination_zipcodes.csv')

# Define how many addresses to generate per zipcode
ADDRESSES_PER_ZIPCODE = 50

# Ensure the output directories exist
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Step 3: Generate random addresses based on geo-shapes
def generate_random_point_within_polygon(polygon):
    minx, miny, maxx, maxy = polygon.bounds
    logging.debug(f"Polygon bounds: {polygon.bounds}")
    while True:
        pnt = Point(random.uniform(minx, maxx), random.uniform(miny, maxy))
        if polygon.contains(pnt):
            logging.debug(f"Generated point within polygon: {pnt}")
            return pnt

# Function to get an address from coordinates using Nominatim with User-Agent and timeout
def get_address_from_coordinates(lat, lon):
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            'lat': lat,
            'lon': lon,
            'format': 'json',
            'addressdetails': 1,
            'zoom': 18
        }
        headers = {
            'User-Agent': 'YourAppName/1.0 (your.email@example.com)'  # Replace with your actual app name and contact email
        }
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            logging.debug(f"Address found for coordinates ({lat}, {lon}): {data.get('display_name', None)}")
            return data.get('display_name', None)
        else:
            logging.error(f"Error fetching address for coordinates ({lat}, {lon}): HTTP {response.status_code}")
            return None
    except requests.exceptions.Timeout:
        logging.error(f"Request timed out for coordinates ({lat}, {lon})")
        return None
    except Exception as e:
        logging.error(f"Error fetching address for coordinates ({lat}, {lon}): {e}")
        return None

def generate_addresses_for_zipcodes(top_zipcodes, geoshapes_df, output_file):
    addresses = []
    for _, row in top_zipcodes.iterrows():
        zip_code = row['ZipCode']
        logging.info(f"Processing ZipCode: {zip_code}")
        geo_shape_row = geoshapes_df[geoshapes_df['PC4'] == zip_code]

        if not geo_shape_row.empty:
            geo_shape = json.loads(geo_shape_row.iloc[0]['Geo Shape'])
            polygon = shape(geo_shape)

            # Generate multiple addresses per zipcode based on ADDRESSES_PER_ZIPCODE
            for _ in range(ADDRESSES_PER_ZIPCODE):
                random_point = generate_random_point_within_polygon(polygon)
                address = get_address_from_coordinates(random_point.y, random_point.x)
                if address:
                    addresses.append({
                        'ZipCode': zip_code,
                        'Latitude': random_point.y,
                        'Longitude': random_point.x,
                        'Address': address
                    })
                    logging.debug(f"Generated address for ZipCode {zip_code}: {address}")
                else:
                    logging.warning(f"No address found for ZipCode {zip_code}.")
        else:
            logging.warning(f"No GeoShape found for ZipCode {zip_code}.")

    addresses_df = pd.DataFrame(addresses)
    addresses_df.to_csv(os.path.join(output_dir, output_file), index=False)
    logging.info(f"Generated addresses saved to {output_file}")

def main():
    # Load geoshapes data and top zip codes
    logging.info("Loading geo-reference data...")
    geoshapes_df = pd.read_csv(georef_file_path)
    
    # Generate random addresses for top origin and destination zipcodes
    logging.info("Generating random addresses for top origin zipcodes...")
    generate_addresses_for_zipcodes(pd.read_csv(top_origin_zipcodes_path), geoshapes_df, 'top_origin_addresses.csv')
    
    logging.info("Generating random addresses for top destination zipcodes...")
    generate_addresses_for_zipcodes(pd.read_csv(top_destination_zipcodes_path), geoshapes_df, 'top_destination_addresses.csv')

if __name__ == "__main__":
    main()
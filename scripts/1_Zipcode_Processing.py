import os
import pandas as pd

# Ensure the script uses its own directory as the working directory
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# Define the paths to the input and output datasets
data_dir = '../data/'
raw_file_path = os.path.join(data_dir, 'raw/georef-netherlands-postcode-pc4.csv')
processed_data_dir = os.path.join(data_dir, 'processed/')
output_dir = os.path.join(data_dir, 'outputs/csv/')

georef_file_path = os.path.join(processed_data_dir, 'cleaned_georef-netherlands-postcode-pc4.csv')

# Ensure the output directories exist
if not os.path.exists(processed_data_dir):
    os.makedirs(processed_data_dir)

# Step 1: Clean and save the geo-reference data
def clean_georef_data(raw_file_path, processed_file_path):
    df = pd.read_csv(raw_file_path, delimiter=';')
    df_cleaned = df[['PC4', 'Geo Point', 'Geo Shape']]
    df_cleaned.to_csv(processed_file_path, index=False)
    print(f"Cleaned dataset saved to {processed_file_path}")

# Step 2: Generate top zip codes and save them
def generate_top_zipcodes(refined_commutes, output_dir):
    total_trips = refined_commutes.shape[0]
    
    top_origin_zipcodes = refined_commutes['OriginZipCode'].value_counts().head(20).reset_index()
    top_origin_zipcodes.columns = ['ZipCode', 'Count']
    top_origin_zipcodes['Percentage'] = (top_origin_zipcodes['Count'] / total_trips) * 100
    top_origin_zipcodes.to_csv(os.path.join(output_dir, 'top_origin_zipcodes.csv'), index=False)
    
    top_destination_zipcodes = refined_commutes['DestinationZipCode'].value_counts().head(20).reset_index()
    top_destination_zipcodes.columns = ['ZipCode', 'Count']
    top_destination_zipcodes['Percentage'] = (top_destination_zipcodes['Count'] / total_trips) * 100
    top_destination_zipcodes.to_csv(os.path.join(output_dir, 'top_destination_zipcodes.csv'), index=False)
    
    print("Top 20 origin and destination zip codes saved.")

def main():
    # Step 1: Clean geo-reference data
    clean_georef_data(raw_file_path, georef_file_path)

    # Load refined commutes data (assuming you have this available)
    refined_commutes = pd.read_csv(os.path.join(processed_data_dir, 'refined_work_related_commutes.csv'))

    # Step 2: Generate top zip codes
    generate_top_zipcodes(refined_commutes, processed_data_dir)

if __name__ == "__main__":
    main()
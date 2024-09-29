import pandas as pd
import os

# Define the paths to the ODIN data file and output directory
data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/'))
file_path = os.path.join(data_dir, 'raw/ODiN2022_Databestand.csv')
output_dir = os.path.join(data_dir, 'processed/')

# Ensure the output directory exists
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

def load_data(file_path, chunk_size=50000):
    """
    Load the ODIN dataset in chunks to handle large files.

    Parameters:
    file_path (str): The path to the dataset.
    chunk_size (int): The size of each chunk to load.

    Returns:
    pd.DataFrame: The concatenated DataFrame of all chunks.
    """
    chunks = []
    try:
        for chunk in pd.read_csv(file_path, chunksize=chunk_size, delimiter=';', encoding='latin1'):
            chunks.append(chunk)
        df = pd.concat(chunks)
        print("Data loaded successfully.")
        return df
    except Exception as e:
        print(f"An error occurred while reading the CSV file: {e}")
        return None

def filter_work_related_commutes(df):
    """
    Filter the dataset to include only work-related commutes.

    Parameters:
    df (pd.DataFrame): The original dataset.

    Returns:
    pd.DataFrame: The filtered DataFrame with relevant columns.
    """
    origin_col = 'VertPC'
    destination_col = 'AankPC'
    trip_purpose_col = 'MotiefV'
    work_related_purposes = ['1', '3']  # Work-related purposes

    # Filter out rows with missing or invalid zip codes and non-work-related purposes
    df_filtered = df[(df[origin_col].notna()) & (df[destination_col].notna()) & 
                     (df[origin_col] != 0) & (df[destination_col] != 0) & 
                     (df[trip_purpose_col].isin(work_related_purposes))]
    return df_filtered

def refine_columns(df_filtered):
    """
    Select and rename the relevant columns for further analysis.

    Parameters:
    df_filtered (pd.DataFrame): The filtered dataset.

    Returns:
    pd.DataFrame: The refined DataFrame with selected columns.
    """
    columns_to_keep = {
        'VertPC': 'OriginZipCode',
        'AankPC': 'DestinationZipCode',
        'Reisduur': 'TravelDuration',
        'Hvm': 'ModeOfTransport'
    }

    refined_commutes = df_filtered[list(columns_to_keep.keys())].rename(columns=columns_to_keep)
    return refined_commutes

def add_time_columns(df_filtered, refined_commutes):
    """
    Combine and add departure and arrival times to the dataset.

    Parameters:
    df_filtered (pd.DataFrame): The filtered dataset with the original time columns.
    refined_commutes (pd.DataFrame): The refined dataset where new time columns will be added.

    Returns:
    pd.DataFrame: The DataFrame with added time columns.
    """
    departure_hour_col = 'VertUur'
    departure_minute_col = 'VertMin'
    arrival_hour_col = 'AankUur'
    arrival_minute_col = 'AankMin'

    refined_commutes['DepartureTime'] = df_filtered[departure_hour_col].astype(str).str.zfill(2) + ':' + df_filtered[departure_minute_col].astype(str).str.zfill(2)
    refined_commutes['ArrivalTime'] = df_filtered[arrival_hour_col].astype(str).str.zfill(2) + ':' + df_filtered[arrival_minute_col].astype(str).str.zfill(2)
    
    return refined_commutes

def map_mode_of_transport(refined_commutes):
    """
    Map mode of transport codes to their descriptions.

    Parameters:
    refined_commutes (pd.DataFrame): The refined dataset with mode of transport codes.

    Returns:
    pd.DataFrame: The DataFrame with mode of transport descriptions.
    """
    mode_of_transport_commuting_mapping = {
        '1': 'Car',
        '2': 'Bus',
        '3': 'Train',
        '4': 'Bike',
        '5': 'Walk',
        '6': 'Tram',
        '7': 'Metro',
        '8': 'Ferry',
        '9': 'Motorcycle',
        '10': 'Scooter',
        '11': 'Electric Bike',
        '12': 'Taxi',
        '13': 'Carpool',
        '14': 'Ride Hailing',
        '15': 'Other',
        '17': 'Speed pedelec',
        '18': 'Cargo bike',
        '19': 'Electric car',
        '20': 'Shared bike',
        '21': 'Shared car',
        '22': 'Moped',
        '23': 'Shared moped',
        '24': 'Other'
    }

    refined_commutes['TransportDescription'] = refined_commutes['ModeOfTransport'].astype(str).map(mode_of_transport_commuting_mapping)
    
    return refined_commutes

def save_refined_data(refined_commutes):
    """
    Save the refined dataset to the output directory.

    Parameters:
    refined_commutes (pd.DataFrame): The refined dataset.
    """
    output_file_path = os.path.join(output_dir, 'refined_work_related_commutes.csv')
    refined_commutes.to_csv(output_file_path, index=False)
    print("Refined work-related commutes data saved.")

def calculate_mode_of_transport_percentages(refined_commutes):
    """
    Calculate the percentage of each mode of transport used for commuting.

    Parameters:
    refined_commutes (pd.DataFrame): The refined dataset.

    Returns:
    pd.DataFrame: The DataFrame with mode of transport percentages.
    """
    mode_of_transport_counts = refined_commutes['ModeOfTransport'].value_counts(normalize=True).reset_index()
    mode_of_transport_counts.columns = ['ModeOfTransport', 'Percentage']
    mode_of_transport_counts['Percentage'] = (mode_of_transport_counts['Percentage'] * 100).round(2)

    mode_of_transport_file_path = os.path.join(output_dir, 'mode_of_transport_commuting_percentages.csv')
    mode_of_transport_counts.to_csv(mode_of_transport_file_path, index=False)
    print("Mode of transport percentages for commuting routes saved.")

    return mode_of_transport_counts

def save_top_zipcodes(refined_commutes, total_trips):
    """
    Find and save the top 10 origin and destination zip codes for work-related commutes.

    Parameters:
    refined_commutes (pd.DataFrame): The refined dataset.
    total_trips (int): The total number of trips.
    """
    top_origin_zipcodes = refined_commutes['OriginZipCode'].value_counts().head(10).reset_index()
    top_origin_zipcodes.columns = ['ZipCode', 'Count']
    top_origin_zipcodes['ZipCode'] = top_origin_zipcodes['ZipCode'].astype(int)  # Convert to integer format
    top_origin_zipcodes['Percentage'] = (top_origin_zipcodes['Count'] / total_trips) * 100

    top_destination_zipcodes = refined_commutes['DestinationZipCode'].value_counts().head(10).reset_index()
    top_destination_zipcodes.columns = ['ZipCode', 'Count']
    top_destination_zipcodes['ZipCode'] = top_destination_zipcodes['ZipCode'].astype(int)  # Convert to integer format
    top_destination_zipcodes['Percentage'] = (top_destination_zipcodes['Count'] / total_trips) * 100

    # Exclude zero zip codes from the results
    top_origin_zipcodes = top_origin_zipcodes[top_origin_zipcodes['ZipCode'] != 0]
    top_destination_zipcodes = top_destination_zipcodes[top_destination_zipcodes['ZipCode'] != 0]

    top_origin_file_path = os.path.join(output_dir, 'top_origin_zipcodes.csv')
    top_destination_file_path = os.path.join(output_dir, 'top_destination_zipcodes.csv')
    
    top_origin_zipcodes.to_csv(top_origin_file_path, index=False)
    top_destination_zipcodes.to_csv(top_destination_file_path, index=False)
    
    print("Top 10 origin and destination zip codes saved.")

def extract_expense_reimbursement_data(df):
    """
    Extract the expense reimbursement data from the dataset.

    Parameters:
    df (pd.DataFrame): The original dataset.

    Returns:
    pd.DataFrame: The DataFrame with expense reimbursement data.
    """
    expense_reimbursement_columns = [
        'WrkVervw',  # Mode of transport with most kilometers to work
        'WrkVerg',   # Receives reimbursement from employer for travel to work
        'VergVast',  # Fixed amount per period
        'VergKm',    # Reimbursement per kilometer driven
        'VergBrSt',  # Fuel cost reimbursement
        'VergOV',    # Public transport subscription reimbursement
        'VergAans',  # Purchase cost reimbursement of the vehicle
        'VergVoer',  # Lease or company vehicle
        'VergBudg',  # Mobility budget
        'VergPark',  # Parking costs reimbursement
        'VergStal',  # Bicycle or moped parking costs reimbursement
        'VergAnd'    # Other reimbursements
    ]

    expense_reimbursement_data = df[expense_reimbursement_columns].dropna()

    expense_reimbursement_file_path = os.path.join(output_dir, 'expense_reimbursement_data.csv')
    expense_reimbursement_data.to_csv(expense_reimbursement_file_path, index=False)
    
    print("Expense reimbursement data saved.")
    return expense_reimbursement_data

def analyze_dataset(df):
    """
    Analyze the entire dataset to understand its structure, column names, and data types.

    Parameters:
    df (pd.DataFrame): The loaded dataset.

    Returns:
    None
    """
    print("\n--- Dataset Information ---")
    print(df.info())

    print("\n--- First 5 Rows of the Dataset ---")
    print(df.head())

    print("\n--- Summary of the Dataset ---")
    print(df.describe(include='all'))

# Add the call to `analyze_dataset` in the `main()` function

def main():
    # Load the dataset
    df = load_data(file_path)
    
    if df is not None:
        # Analyze the dataset
        analyze_dataset(df)
        
        # Filter work-related commutes
        df_filtered = filter_work_related_commutes(df)
        
        # Refine and process the columns
        refined_commutes = refine_columns(df_filtered)
        refined_commutes = add_time_columns(df_filtered, refined_commutes)
        refined_commutes = map_mode_of_transport(refined_commutes)
        
        # Save the refined work-related commutes data
        save_refined_data(refined_commutes)
        
        # Calculate and save mode of transport percentages
        mode_of_transport_counts = calculate_mode_of_transport_percentages(refined_commutes)
        
        # Save the top origin and destination zip codes
        total_trips = refined_commutes.shape[0]
        save_top_zipcodes(refined_commutes, total_trips)
        
        # Extract and save expense reimbursement data
        extract_expense_reimbursement_data(df)
        
        # Debug: Print summaries
        print("Refined Dataset Summary:")
        print(refined_commutes.info())
        print(refined_commutes.head())
        
        print("Mode of transport percentages:")
        print(mode_of_transport_counts.head())

if __name__ == "__main__":
    main()
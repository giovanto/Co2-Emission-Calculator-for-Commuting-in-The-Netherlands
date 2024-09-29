import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from geopy.distance import geodesic
from datetime import datetime
import adjustText as aT

# Ensure the script uses its own directory as the working directory
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# Define the paths to the datasets
data_dir = '../data/processed/'
output_dir = '../data/outputs/graphs/'

# File paths
mode_of_transport_path = os.path.join(data_dir, 'mode_of_transport_commuting_percentages.csv')
refined_commutes_path = os.path.join(data_dir, 'refined_work_related_commutes.csv')
zipcode_coordinates_path = os.path.join(data_dir, 'cleaned_georef-netherlands-postcode-pc4.csv')

# Ensure the output directory exists
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Load the datasets
mode_of_transport_df = pd.read_csv(mode_of_transport_path)
refined_commutes = pd.read_csv(refined_commutes_path)
zipcode_coordinates = pd.read_csv(zipcode_coordinates_path)

# Define mode categories and their colors
mode_categories = {
    'Public Transport': ['Bus', 'Train', 'Metro', 'Tram', 'Ferry'],
    'Shared Mobility': ['Carpool', 'Shared bike', 'Shared car', 'Shared moped', 'Ride Hailing', 'Moped'],
    'Active Mobility': ['Bike', 'Walk', 'Electric Bike', 'Speed pedelec', 'Scooter', 'Cargo bike'],
    'Passive Mobility': ['Car', 'Taxi', 'Motorcycle', 'Electric car']
}

mode_category_colors = {
    'Public Transport': '#1f77b4',  # Blue
    'Shared Mobility': '#ff7f0e',   # Orange
    'Active Mobility': '#2ca02c',   # Green
    'Passive Mobility': '#d62728'   # Red
}

def get_mode_category_color(mode):
    for category, modes in mode_categories.items():
        if mode in modes:
            return mode_category_colors[category]
    return '#7f7f7f'  # Default color for 'Other'

def categorize_mode(mode):
    for category, modes in mode_categories.items():
        if mode in modes:
            return category
    return 'Other'

# ------------------------------------------------------------------------------
# Section 1: Share of Transportation Modes for Commuting
# ------------------------------------------------------------------------------

# Create a dictionary to map mode of transport codes to descriptions
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

# Map mode of transport codes to descriptions
mode_of_transport_df['ModeOfTransport'] = mode_of_transport_df['ModeOfTransport'].astype(str).map(mode_of_transport_commuting_mapping)
refined_commutes['ModeOfTransport'] = refined_commutes['ModeOfTransport'].astype(str).map(mode_of_transport_commuting_mapping)

# Filter out transport modes with less than 1% share
small_modes = mode_of_transport_df[mode_of_transport_df['Percentage'] < 1]
large_modes = mode_of_transport_df[mode_of_transport_df['Percentage'] >= 1]

# Set the style
sns.set(style="whitegrid")

# Create a pie chart
plt.figure(figsize=(12, 12))
wedges, texts, autotexts = plt.pie(large_modes['Percentage'], labels=large_modes['ModeOfTransport'],
                                   autopct='%1.1f%%', startangle=140, colors=[get_mode_category_color(mode) for mode in large_modes['ModeOfTransport']], pctdistance=0.85)

# Add a white circle in the center to create a donut chart
centre_circle = plt.Circle((0, 0), 0.70, fc='white')
fig = plt.gcf()
fig.gca().add_artist(centre_circle)

# Adjust text properties
for text in texts:
    text.set_fontsize(14)
    text.set_color('black')
for autotext in autotexts:
    autotext.set_fontsize(12)
    autotext.set_color('white')

# Create legend for small modes
legend_labels = [row['ModeOfTransport'] for _, row in small_modes.iterrows() if row['ModeOfTransport'] != 'nan']
plt.legend(legend_labels, loc='upper left', bbox_to_anchor=(1, 1), title="Less than 1%", fontsize=12)

# Save the plot
output_file_path = os.path.join(output_dir, 'share_of_transport_modes_for_commuting.png')
plt.savefig(output_file_path, bbox_inches='tight')
print(f"Chart saved to {output_file_path}")

import matplotlib.patches as mpatches

# ------------------------------------------------------------------------------
# Section 2: Average Travel Duration by Mode of Transport
# ------------------------------------------------------------------------------

# Convert TravelDuration to numeric, setting errors='coerce' will turn invalid parsing into NaN
refined_commutes['TravelDuration'] = pd.to_numeric(refined_commutes['TravelDuration'], errors='coerce')

# Calculate the average travel duration by mode of transport
avg_travel_duration = refined_commutes.groupby('ModeOfTransport')['TravelDuration'].mean().reset_index()

# Add category and sort
avg_travel_duration['Category'] = avg_travel_duration['ModeOfTransport'].apply(categorize_mode)
avg_travel_duration = avg_travel_duration.sort_values(by=['Category', 'TravelDuration'], ascending=[True, False])

# Plot the average travel duration (use a simple palette or default color scheme)
plt.figure(figsize=(12, 8))
ax = sns.barplot(x='ModeOfTransport', y='TravelDuration', data=avg_travel_duration, errorbar=None)

# Add an average line for reference
plt.axhline(y=refined_commutes['TravelDuration'].mean(), color='r', linestyle='--', label='Overall Average')

# Add title and labels
plt.title('Average Travel Duration by Mode of Transport')
plt.xlabel('Mode of Transport')
plt.ylabel('Average Travel Duration (minutes)')
plt.xticks(rotation=45)

# Create patches for the legend (without color mapping)
active_patch = mpatches.Patch(color='green', label='Active Mobility')
public_patch = mpatches.Patch(color='blue', label='Public Transport')
passive_patch = mpatches.Patch(color='red', label='Passive Mobility')
shared_patch = mpatches.Patch(color='orange', label='Shared Mobility')

# Add the legend, as shown in your screenshot
plt.legend(handles=[active_patch, public_patch, passive_patch, shared_patch], title="Mode\nCategory", loc='upper right')

# Tight layout for better spacing and save the figure
plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'avg_travel_duration_with_legend.png'))

print("Chart with custom legend saved.")
# ------------------------------------------------------------------------------
# Section 3: Distribution of Departure and Arrival Times
# ------------------------------------------------------------------------------

# Convert DepartureTime and ArrivalTime to datetime
refined_commutes['DepartureTime'] = pd.to_datetime(refined_commutes['DepartureTime'], format='%H:%M', errors='coerce')
refined_commutes['ArrivalTime'] = pd.to_datetime(refined_commutes['ArrivalTime'], format='%H:%M', errors='coerce')

# Extract the hour from the datetime to analyze rush hours
refined_commutes['DepartureHour'] = refined_commutes['DepartureTime'].dt.hour
refined_commutes['ArrivalHour'] = refined_commutes['ArrivalTime'].dt.hour

# Plot the distribution of departure times
plt.figure(figsize=(12, 8))
sns.histplot(refined_commutes['DepartureHour'], bins=24, kde=True, color='blue')
plt.xlabel('Hour of the Day')
plt.ylabel('Frequency of Trips')
plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'departure_times.png'))

print("Departure Times chart saved.")

# Plot the distribution of arrival times
plt.figure(figsize=(12, 8))
sns.histplot(refined_commutes['ArrivalHour'], bins=24, kde=True, color='green')
plt.xlabel('Hour of the Day')
plt.ylabel('Frequency of Trips')
plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'arrival_times.png'))

print("Arrival Times chart saved.")

# ------------------------------------------------------------------------------
# Section 4: Average Distance by Mode of Transport
# ------------------------------------------------------------------------------

# Function to calculate geodesic distance
def calculate_distance(row):
    origin_coords = (row['lat_origin'], row['lon_origin'])
    destination_coords = (row['lat_destination'], row['lon_destination'])
    return geodesic(origin_coords, destination_coords).kilometers

# Split 'Geo Point' into separate latitude and longitude columns
zipcode_coordinates[['lat', 'lon']] = zipcode_coordinates['Geo Point'].str.split(', ', expand=True)

# Convert latitude and longitude to float
zipcode_coordinates['lat'] = zipcode_coordinates['lat'].astype(float)
zipcode_coordinates['lon'] = zipcode_coordinates['lon'].astype(float)

# Rename columns for merging
zipcode_coordinates = zipcode_coordinates.rename(columns={'PC4': 'OriginZipCode', 'lat': 'lat_origin', 'lon': 'lon_origin'})

# Merge the coordinates with the refined_commutes dataset for origin
refined_commutes = refined_commutes.merge(zipcode_coordinates[['OriginZipCode', 'lat_origin', 'lon_origin']], on='OriginZipCode', how='left')

# Rename columns for merging destination coordinates
zipcode_coordinates = zipcode_coordinates.rename(columns={'OriginZipCode': 'DestinationZipCode', 'lat_origin': 'lat_destination', 'lon_origin': 'lon_destination'})

# Merge the coordinates with the refined_commutes dataset for destination
refined_commutes = refined_commutes.merge(zipcode_coordinates[['DestinationZipCode', 'lat_destination', 'lon_destination']], on='DestinationZipCode', how='left')

# Calculate distances
refined_commutes['Distance'] = refined_commutes.apply(calculate_distance, axis=1)

# Calculate the average distance per mode of transport
avg_distance = refined_commutes.groupby('ModeOfTransport')['Distance'].mean().reset_index()

# Add category and sort
avg_distance['Category'] = avg_distance['ModeOfTransport'].apply(categorize_mode)
avg_distance = avg_distance.sort_values(by=['Category', 'Distance'], ascending=[True, False])

# Plot the average distance
plt.figure(figsize=(12, 8))
sns.barplot(x='ModeOfTransport', y='Distance', data=avg_distance, palette=[get_mode_category_color(mode) for mode in avg_distance['ModeOfTransport']], errorbar=None)
plt.axhline(y=refined_commutes['Distance'].mean(), color='r', linestyle='--', label='Average Distance')
plt.xlabel('Mode of Transport')
plt.ylabel('Average Distance (km)')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'avg_distance.png'))

print("Average Distance chart saved.")

# ------------------------------------------------------------------------------
# Section 5: Improved Visualization of Distance, Time, and Speed by Transport Mode
# ------------------------------------------------------------------------------

# Calculate average travel duration, distance, and speed per mode of transport
refined_commutes['TravelDuration'] = pd.to_numeric(refined_commutes['TravelDuration'], errors='coerce')
refined_commutes['Distance'] = pd.to_numeric(refined_commutes['Distance'], errors='coerce')
refined_commutes = refined_commutes.dropna(subset=['TravelDuration', 'Distance'])

# Calculate average speed (Distance / Travel Duration in hours)
refined_commutes['Speed'] = refined_commutes['Distance'] / (refined_commutes['TravelDuration'] / 60)

# Group by ModeOfTransport and calculate means
avg_stats = refined_commutes.groupby('ModeOfTransport').agg({
    'TravelDuration': 'mean',
    'Distance': 'mean',
    'Speed': 'mean'
}).reset_index()

# Add a category column to avg_stats
avg_stats['Category'] = avg_stats['ModeOfTransport'].apply(categorize_mode)

# Define the colors for each category
category_colors = {
    'Active Mobility': '#2ca02c',   # Green
    'Public Transport': '#1f77b4',  # Blue
    'Passive Mobility': '#d62728',  # Red
    'Shared Mobility': '#ff7f0e',   # Orange
    'Other': '#7f7f7f'              # Grey
}

# Set the style
sns.set(style="whitegrid")

# Create the scatter plot
plt.figure(figsize=(16, 12))
ax = sns.scatterplot(
    data=avg_stats,
    x='TravelDuration',
    y='Distance',
    hue='Category',
    size='Speed',
    sizes=(100, 2000),
    legend='full',
    palette=category_colors,
    alpha=0.7
)

# Annotate the points without overlapping
for line in range(0, avg_stats.shape[0]):
    plt.text(
        avg_stats.TravelDuration[line],
        avg_stats.Distance[line],
        avg_stats.ModeOfTransport[line],
        fontsize=10,
        verticalalignment='bottom'
    )

# Add the y=x line representing equal speed
plt.plot([0, 80], [0, 80], linestyle='--', color='grey')

# Add the legend
handles, labels = ax.get_legend_handles_labels()
category_legend = ax.legend(
    handles[:5], labels[:5], loc='upper left', title='Mode'
)

# Create a custom legend for the bubble sizes
speed_ranges = ['< 10 km/h', '10-20 km/h', '20-30 km/h', '> 30 km/h']
size_handles = [
    plt.Line2D([0], [0], marker='o', color='w', label=speed_ranges[i],
               markersize=10 + (i*5), markerfacecolor='k', alpha=0.7)
    for i in range(4)
]
size_legend = plt.legend(size_handles, speed_ranges, loc='upper right', title='Average Speed (km/h)', fontsize=10, labelspacing=1.7)

plt.gca().add_artist(category_legend)
plt.gca().add_artist(size_legend)

plt.xlabel('Average Travel Duration (minutes)')
plt.ylabel('Average Distance (km)')
plt.xlim(0, 80)
plt.ylim(0, 50)
plt.tight_layout()

# Save the plot
output_file_path = os.path.join(output_dir, 'avg_travel_distance_speed_bubble.png')
plt.savefig(output_file_path, bbox_inches='tight')
print(f"Chart saved to {output_file_path}")
import pandas as pd

# Source: Data from the 2023 vehicle registry, RDW Netherlands

# Direct input of values for 2023 M1 vehicles based on the provided data
vehicle_data_2023 = {
    'Fuel type': ['Alcohol and alcohol hybrid', 'Petrol and petrol hybrid', 'CNG and CNG hybrid', 'Diesel and diesel hybrid',
                  'FEV', 'LNG and LNG hybrid', 'LPG and LPG hybrid', 'PHEV petrol', 'PHEV diesel', 'Hydrogen and hydrogen hybrid'],
    'Number': [3752, 7401993, 8279, 867185, 328486, 6, 95269, 168667, 12176, 594]
}

# Create a DataFrame from the above values
df_2023 = pd.DataFrame(vehicle_data_2023)

# Total number of M1 vehicles in 2023 (from the provided data)
total_vehicles = 8886407

# Calculate percentage composition per fuel type
df_2023['Percentage'] = df_2023['Number'] / total_vehicles * 100

# Define the WPM TTW CO2 emission factors for each fuel type (gCO2 per km)
# These values are based on WPM emission factors
emission_factors = {
    'Petrol and petrol hybrid': 147,
    'Diesel and diesel hybrid': 127,
    'PHEV petrol': 116,  # Plug-in Hybrid
    'FEV': 0,  # Full Electric is 0 gCO2/km according to WPM
    'LPG and LPG hybrid': 129,
    'CNG and CNG hybrid': 110,
    'Hydrogen and hydrogen hybrid': 0,  # Treated as zero emissions
    'PHEV diesel': 96,
    'LNG and LNG hybrid': 96,
    'Alcohol and alcohol hybrid': 36  # Assuming E85-like values for alcohol
}

# Assign emission factors to the fuel types
df_2023['CO2_factor'] = df_2023['Fuel type'].map(emission_factors)

# Calculate the weighted average CO2 emissions
df_2023['Weighted_CO2'] = df_2023['Percentage'] * df_2023['CO2_factor'] / 100
average_co2_emission = df_2023['Weighted_CO2'].sum()

# Print the result
print(f"Average TTW CO2 emission for M1 vehicles in 2023: {average_co2_emission:.2f} gCO2/km")

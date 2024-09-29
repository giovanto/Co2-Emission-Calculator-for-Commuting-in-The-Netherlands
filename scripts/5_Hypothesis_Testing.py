import os
import pandas as pd
from scipy import stats
import numpy as np

# Set the working directory
script_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(script_dir, '../data/outputs/csv/')
input_file_path = os.path.join(data_dir, 'simplified_co2_emissions_summary.csv')

# Load the data
df = pd.read_csv(input_file_path)

# Helper functions for hypothesis testing
def paired_t_test(group1, group2):
    """Conducts a paired t-test for two related samples"""
    t_stat, p_value = stats.ttest_rel(group1, group2)
    return t_stat, p_value

def independent_t_test(group1, group2):
    """Conducts an independent t-test for two unrelated samples"""
    t_stat, p_value = stats.ttest_ind(group1, group2, nan_policy='omit')
    return t_stat, p_value

def anova_test(*groups):
    """Conducts a one-way ANOVA test"""
    f_stat, p_value = stats.f_oneway(*groups)
    return f_stat, p_value

def f_test(group1, group2):
    """Conducts an F-test for comparing variances between two groups"""
    f_stat = np.var(group1, ddof=1) / np.var(group2, ddof=1)
    dfn = len(group1) - 1
    dfd = len(group2) - 1
    p_value = 1 - stats.f.cdf(f_stat, dfn, dfd)
    return f_stat, p_value

# Hypothesis Testing

# H1: Paired t-test for CO2 emissions (WPM TTW vs WTW) across commute distances
print("H1: Paired t-test for CO2 emissions (WPM TTW vs WTW)")

# Use the 'commute_distance_group' column instead of defining new distance groups
commute_groups = ['short', 'medium', 'long']

# Paired t-test for short, medium, and long commutes
for group in commute_groups:
    filtered_df = df[df['commute_distance_group'] == group]
    if len(filtered_df) > 1:
        t_stat, p_value = paired_t_test(filtered_df['total_co2_emissions_TTW_g'], filtered_df['total_co2_emissions_WTW_g'])
        print(f"{group.capitalize()} commutes: T-stat = {t_stat:.4f}, P-value = {p_value:.4f}")
    else:
        print(f"{group.capitalize()} commutes: Not enough data for paired t-test.")

# H2: Independent t-test for CO2 emissions (Multimodal vs Car-only)
print("\nH2: Independent t-test for CO2 emissions (Multimodal vs Car-only)")
car_only_trips = df[df['mode'] == 'CAR']
multimodal_trips = df[df['is_multimodal'] == True]  # Using is_multimodal column to define multimodal trips
for method in ['total_co2_emissions_TTW_g', 'total_co2_emissions_WTW_g']:
    t_stat, p_value = independent_t_test(multimodal_trips[method], car_only_trips[method])
    print(f"CO2 emissions ({method}) - T-stat = {t_stat:.4f}, P-value = {p_value:.4f}")

# H3: Independent t-test for CO2 emissions per minute (Multimodal vs Car-only)
print("\nH3: CO2 emissions per minute (Multimodal vs Car-only)")
multimodal_trips = df[df['is_multimodal'] == True]
car_only_trips = df[df['mode'] == 'CAR']

# Filter out zero or missing values for the t-test
for method in ['co2_per_minute_TTW_g', 'co2_per_minute_WTW_g']:
    multimodal_trips_valid = multimodal_trips[(multimodal_trips[method] > 0) & multimodal_trips[method].notna()]
    car_only_trips_valid = car_only_trips[(car_only_trips[method] > 0) & car_only_trips[method].notna()]
    if len(multimodal_trips_valid) > 1 and len(car_only_trips_valid) > 1:
        t_stat, p_value = independent_t_test(multimodal_trips_valid[method], car_only_trips_valid[method])
        print(f"CO2 per minute ({method}) - T-stat = {t_stat:.4f}, P-value = {p_value:.4f}")
    else:
        print(f"Not enough valid data for {method}")

# H4: Independent t-test for CO2 emissions (Bicycles vs Other Modes)
print("\nH4: Independent t-test for CO2 emissions (Bicycles vs Other Modes)")
bicycle_trips = df[df['mode'] == 'BICYCLE']
other_trips = df[df['mode'] != 'BICYCLE']  # All other modes excluding Bicycles
for method in ['total_co2_emissions_TTW_g', 'total_co2_emissions_WTW_g']:
    t_stat, p_value = independent_t_test(bicycle_trips[method], other_trips[method])
    print(f"CO2 emissions ({method}) - T-stat = {t_stat:.4f}, P-value = {p_value:.4f}")

# H5: Correlation between trip duration and CO2 emissions for car trips
car_trips = df[df['mode'] == 'CAR']

print("\nH5: Correlation between trip duration and CO2 emissions for car trips")
for method in ['total_co2_emissions_TTW_g', 'total_co2_emissions_WTW_g']:
    corr, p_value = stats.pearsonr(car_trips['total_duration_min'], car_trips[method])
    print(f"CO2 emissions ({method}) - Correlation = {corr:.4f}, P-value = {p_value:.4f}")

# H6: One-way ANOVA for short commutes (<10 km)
short_commutes = df[df['commute_distance_group'] == 'short']
modes = ['BICYCLE', 'CAR', 'TRANSIT']

print("\nH6: One-way ANOVA for CO2 emissions (Cycling vs Car vs Transit for short commutes)")
for method in ['total_co2_emissions_TTW_g', 'total_co2_emissions_WTW_g']:
    groups = [short_commutes[short_commutes['mode'] == mode][method] for mode in modes]
    f_stat, p_value = anova_test(*groups)
    print(f"CO2 emissions ({method}) - F-stat = {f_stat:.4f}, P-value = {p_value:.4f}")

# H7: F-test for CO2 emissions variance (Multimodal vs Unimodal for all distance groups based on total_km)
for group in commute_groups:
    filtered_df = df[df['commute_distance_group'] == group]
    multimodal_commutes = filtered_df[filtered_df['is_multimodal'] == True]
    unimodal_commutes = filtered_df[filtered_df['is_multimodal'] == False]

    print(f"\nH7: F-test for variance in CO2 emissions (Multimodal vs Unimodal for {group} commutes)")
    for method in ['total_co2_emissions_TTW_g', 'total_co2_emissions_WTW_g']:
        if len(multimodal_commutes) > 1 and len(unimodal_commutes) > 1:
            f_stat, p_value = f_test(multimodal_commutes[method], unimodal_commutes[method])
            print(f"CO2 emissions ({method}) - F-stat = {f_stat:.4f}, P-value = {p_value:.4f}")
        else:
            print(f"Not enough data for F-test in {method} for {group} commutes")

# H8: Linear regression for CO2 emissions per kilometer
df['co2_per_km_TTW_g'] = df['total_co2_emissions_TTW_g'] / df['total_km']
df['co2_per_km_WTW_g'] = df['total_co2_emissions_WTW_g'] / df['total_km']

print("\nH8: Linear regression for CO2 emissions per kilometer")
for method in ['co2_per_km_TTW_g', 'co2_per_km_WTW_g']:
    # Set up independent variables: total_km, mode, total_duration_min
    df['mode_is_car'] = df['mode'].apply(lambda x: 1 if x == 'CAR' else 0)
    df['mode_is_transit'] = df['mode'].apply(lambda x: 1 if x == 'TRANSIT' else 0)

    X = df[['total_km', 'mode_is_car', 'mode_is_transit', 'total_duration_min']]
    y = df[method]

    # Perform linear regression
    # Implement the regression logic here
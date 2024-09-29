import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import squarify

# Ensure the script uses its own directory as the working directory
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# Define the paths to the datasets
data_dir = '../data/processed/'
output_dir = '../data/outputs/graphs/'

# File paths
expense_reimbursement_path = os.path.join(data_dir, 'expense_reimbursement_data.csv')

# Load the datasets
expense_data = pd.read_csv(expense_reimbursement_path)

# Function to map mode of transport codes to descriptions
def map_transport_mode(code):
    mode_mapping = {
        1: 'On foot',
        2: 'Bicycle/Electric Bicycle/Speed Pedelec',
        3: 'Moped/Scooter',
        4: 'Passenger Car',
        5: 'Van',
        6: 'Motor',
        7: 'Train',
        8: 'Bus/Tram/Metro',
        9: 'Other',
        10: 'Unknown',
        11: 'Work from Home',
        12: 'No Paid Work',
        13: 'Under 15 years old'
    }
    return mode_mapping.get(code, 'Unknown')

# Map transport mode codes to descriptions
expense_data['WrkVervw'] = expense_data['WrkVervw'].apply(map_transport_mode)

# Reimbursement type labels
reimbursement_labels = {
    'VergVast': 'Fixed Amount',
    'VergKm': 'Per Kilometer',
    'VergBrSt': 'Fuel Costs',
    'VergOV': 'Public Transport',
    'VergAans': 'Purchase Costs',
    'VergVoer': 'Lease/Company Vehicle',
    'VergBudg': 'Mobility Budget',
    'VergPark': 'Parking Costs',
    'VergStal': 'Bicycle/Moped Parking',
    'VergAnd': 'Other'
}

# Plot 1: Improved Donut chart for percentage of respondents receiving any form of reimbursement
reimbursement_counts = expense_data['WrkVerg'].value_counts(normalize=True) * 100
reimbursement_counts.index = ['No Reimbursement', 'Reimbursement', 'Not Applicable']

fig, ax = plt.subplots(figsize=(8, 8))
wedges, texts, autotexts = ax.pie(reimbursement_counts, labels=reimbursement_counts.index, autopct='%1.1f%%', startangle=140, colors=sns.color_palette('pastel'), wedgeprops=dict(width=0.3, edgecolor='w'))

for i, wedge in enumerate(wedges):
    plt.setp(autotexts[i], size=10, weight="bold")
    plt.setp(texts[i], size=12)

# Save the donut chart
donut_chart_path = os.path.join(output_dir, 'reimbursement_percentage_donut.png')
plt.savefig(donut_chart_path)

# Plot 2: Improved Treemap for distribution of different reimbursement types
reimbursement_types = ['VergVast', 'VergKm', 'VergBrSt', 'VergOV', 'VergAans', 'VergVoer', 'VergBudg', 'VergPark', 'VergStal', 'VergAnd']
reimbursement_counts = expense_data[reimbursement_types].apply(pd.Series.value_counts).loc[1].fillna(0)
reimbursement_counts.index = [reimbursement_labels[key] for key in reimbursement_counts.index]

fig, ax = plt.subplots(figsize=(12, 8))
squarify.plot(sizes=reimbursement_counts.values, label=reimbursement_counts.index, alpha=0.8, color=sns.color_palette('viridis', len(reimbursement_counts)), ax=ax, pad=True)
ax.axis('off')
plt.tight_layout()

# Save the treemap
treemap_path = os.path.join(output_dir, 'reimbursement_treemap.png')
plt.savefig(treemap_path)

# Plot 3: Improved Heatmap for correlation between different types of reimbursements and modes of transport
# Filter out specific transport modes
filtered_modes = ['On foot', 'Other', 'No Paid Work', 'Under 15 years old', 'Unknown', 'Work from Home']
heatmap_data = expense_data[~expense_data['WrkVervw'].isin(filtered_modes)][reimbursement_types + ['WrkVervw']]
heatmap_data = heatmap_data.replace({0: 0, 1: 1, 2: 2}).groupby('WrkVervw').mean()

# Update axis labels for better readability
heatmap_data = heatmap_data.rename(columns=reimbursement_labels)

fig, ax = plt.subplots(figsize=(14, 10))
sns.heatmap(heatmap_data.T, annot=True, cmap='coolwarm', cbar_kws={'label': 'Average Reimbursement Rate'}, ax=ax)
ax.set_xlabel('Transport Modes')
ax.set_ylabel('Reimbursement Types')
ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
plt.tight_layout()

# Save the heatmap
heatmap_path = os.path.join(output_dir, 'correlation_heatmap.png')
plt.savefig(heatmap_path)

print("Graphs created and saved.")
import pandas as pd
import matplotlib.pyplot as plt

def plot_carbon_intensity(carbon_intensity_data_path, month_to_analyze):
    # Load the carbon intensity data
    carbon_intensity_data = pd.read_csv(carbon_intensity_data_path)
    carbon_intensity_data['Datetime (UTC)'] = pd.to_datetime(carbon_intensity_data['Datetime (UTC)'])

    # Filter carbon intensity data for the specified month
    carbon_intensity_data = carbon_intensity_data[carbon_intensity_data['Datetime (UTC)'].dt.month == month_to_analyze]

    # Resample the carbon intensity data to daily values and keep only numeric columns
    numeric_columns = carbon_intensity_data.select_dtypes(include=['number']).columns
    carbon_intensity_data_daily = carbon_intensity_data.set_index('Datetime (UTC)')[numeric_columns].resample('D').mean().reset_index()

    # Plot the carbon intensity data
    plt.figure(figsize=(10, 6))
    plt.plot(carbon_intensity_data_daily['Datetime (UTC)'], carbon_intensity_data_daily['Carbon Intensity gCO₂eq/kWh (direct)'], marker='o')
    plt.xlabel('Day')
    plt.ylabel('Carbon Intensity (gCO2e/kWh)')
    plt.title('Daily Carbon Intensity of the Grid')
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('carbon_intensity_of_grid.pdf', format='pdf')
    plt.show()

# Example usage
carbon_intensity_data_path = 'NL_2023_daily.csv'
month_to_analyze = 1  # January

plot_carbon_intensity(carbon_intensity_data_path, month_to_analyze)

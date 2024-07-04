import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import os

def analyse_months_emissions(data_csv_path, traffic_data_path, carbon_intensity_data_path, month_to_analyze, days_in_month):
    # Load the website data with the correct delimiter
    website_data = pd.read_csv(data_csv_path, delimiter=';')

    # Print column names to debug
    print("Columns in website_data:", website_data.columns)

    # Check if 'monthly_visits_mil' column exists
    if 'monthly_visits_mil' not in website_data.columns:
        raise KeyError("'monthly_visits_mil' column not found in website_data")

    # Convert 'monthly_visits_mil' column to numeric
    website_data['monthly_visits_mil'] = pd.to_numeric(website_data['monthly_visits_mil'], errors='coerce')

    # Load the traffic data with the correct delimiter
    traffic_data = pd.read_csv(traffic_data_path, delimiter=';')

    # Rename columns directly
    traffic_data.columns = ['Day', 'Amazon', 'Bol.com', 'Coolblue', 'Zalando', 'IKEA', 'NU.nl',
                            'Algemeen Dagblad', 'De Telegraaf', 'De Volkskrant', 'RTL Nieuws',
                            'University of Amsterdam', 'Delft University of Technology (TU Delft)',
                            'University of Groningen', 'Utrecht University', 'Erasmus University Rotterdam',
                            'Google Chrome', 'Microsoft Bing', 'Yahoo', 'DuckDuckGo']

    # Print column names to debug
    print("Columns in traffic_data:", traffic_data.columns)

    # Check if 'Day' column exists
    if 'Day' not in traffic_data.columns:
        raise KeyError("'Day' column not found in traffic_data")

    traffic_data['Day'] = pd.to_datetime(traffic_data['Day'], format='%Y-%m-%d', errors='coerce')

    carbon_intensity_data = pd.read_csv(carbon_intensity_data_path)

    carbon_intensity_data['Datetime (UTC)'] = pd.to_datetime(carbon_intensity_data['Datetime (UTC)'])

    # Filter carbon intensity data for the specified month
    carbon_intensity_data = carbon_intensity_data[carbon_intensity_data['Datetime (UTC)'].dt.month == month_to_analyze]

    # Resample the carbon intensity data to daily values and keep only numeric columns
    numeric_columns = carbon_intensity_data.select_dtypes(include=['number']).columns
    carbon_intensity_data_daily = carbon_intensity_data.set_index('Datetime (UTC)')[numeric_columns].resample('D').mean().reset_index()

    categories = {
        'E-commerce': ['Amazon', 'Zalando', 'IKEA', 'Bol.com', 'Coolblue'],
        'News': ['NU.nl', 'Algemeen Dagblad', 'De Telegraaf', 'De Volkskrant', 'RTL Nieuws'],
        'Universities': ['University of Amsterdam', 'Delft University of Technology (TU Delft)',
                         'University of Groningen', 'Utrecht University', 'Erasmus University Rotterdam'],
        'Search Engines': ['Google Chrome', 'Microsoft Bing', 'Yahoo', 'DuckDuckGo']
    }

    # Create separate figures for traffic and emissions plots
    fig_traffic, axs_traffic = plt.subplots(4, 1, figsize=(20, 40))
    fig_emissions, axs_emissions = plt.subplots(4, 1, figsize=(20, 40))
    axs_traffic = axs_traffic.flatten()
    axs_emissions = axs_emissions.flatten()

    # Get distinct colors for each website
    color_map = cm.get_cmap('tab20')
    website_colors = {}
    color_idx = 0

    for category, websites in categories.items():
        for website in websites:
            if website not in website_colors:
                website_colors[website] = color_map(color_idx)
                color_idx += 1

    # Find the maximum emission value for each category separately
    max_emission_values = {category: 0 for category in categories}

    emission_data_by_category = {}

    for category, websites in categories.items():
        for website in websites:
            if website in website_data['Website'].values and website in traffic_data.columns:
                # Step 1: Determine the website with the most uniform Google Trends values
                variances = {website: traffic_data[website].var() for website in websites if website in traffic_data.columns}
                reference_website = min(variances, key=variances.get)
                reference_website_name = reference_website

                # Step 2: Calculate average daily visits for the reference website
                total_monthly_visits_reference = website_data.loc[website_data['Website'] == reference_website_name, 'monthly_visits_mil'].values[0] * 1e6
                average_daily_visits_reference = total_monthly_visits_reference / days_in_month

                # Step 3: Calculate the average Google Trends value for the reference website
                average_trends_value_reference = traffic_data[reference_website].mean()

                # Step 4: Calculate visits per Google Trends point
                visits_per_trend_point = average_daily_visits_reference / average_trends_value_reference

                # Step 5: Calculate absolute visitors for each website
                traffic_data[f'{website}_Absolute_Visitors'] = traffic_data[website] * visits_per_trend_point

                # Merge traffic data with carbon intensity data
                merged_data = pd.merge(traffic_data, carbon_intensity_data_daily, left_on='Day', right_on='Datetime (UTC)')

                # Calculate daily carbon emissions
                merged_data[f'{website}_Carbon_Emissions'] = (
                        merged_data[f'{website}_Absolute_Visitors'] *
                        website_data.loc[website_data['Website'] == website, 'kWh'].values[0] *
                        (merged_data['Carbon Intensity gCO₂eq/kWh (direct)'] / 1000)
                )

                # Track the maximum emission value for the category
                max_emission_values[category] = max(max_emission_values[category], merged_data[f'{website}_Carbon_Emissions'].max())

                # Store emission data by category for later plotting
                if category not in emission_data_by_category:
                    emission_data_by_category[category] = {}
                emission_data_by_category[category][website] = merged_data

    for idx, (category, websites) in enumerate(categories.items()):
        # Plot Google Trends traffic data
        ax_traffic = axs_traffic[idx]

        for website in websites:
            if website in traffic_data.columns:
                ax_traffic.plot(traffic_data['Day'], traffic_data[website], marker='o', label=f'{website}', color=website_colors[website])

        ax_traffic.set_xlabel('Day')
        ax_traffic.set_ylabel('Google Trends Traffic')
        ax_traffic.set_title(f'{category} - Traffic')
        ax_traffic.legend()
        ax_traffic.grid(True)
        plt.setp(ax_traffic.xaxis.get_majorticklabels(), rotation=45)

        # Plot carbon emissions data
        ax_emissions = axs_emissions[idx]

        for website in websites:
            if category in emission_data_by_category and website in emission_data_by_category[category]:
                merged_data = emission_data_by_category[category][website]
                ax_emissions.plot(merged_data['Day'], merged_data[f'{website}_Carbon_Emissions'], marker='o', label=f'{website}', color=website_colors[website])

        ax_emissions.set_xlabel('Day')
        ax_emissions.set_ylabel('Carbon Emissions (kg CO2e)')
        ax_emissions.set_title(f'{category} - Emissions')
        ax_emissions.legend()
        ax_emissions.grid(True)
        ax_emissions.set_ylim(0, max_emission_values[category])
        plt.setp(ax_emissions.xaxis.get_majorticklabels(), rotation=45)

    fig_traffic.tight_layout()
    fig_emissions.tight_layout()
    fig_traffic.savefig('monthly_traffic_analysis.pdf', format='pdf')
    fig_emissions.savefig('monthly_emissions_analysis.pdf', format='pdf')
    plt.show()

# Example usage
data_csv_path = 'kwh_browsing_session.csv'
traffic_data_path = 'january_all.csv'
carbon_intensity_data_path = 'NL_2023_daily.csv'
month_to_analyze = 1  # January
days_in_month = 31

analyse_months_emissions(data_csv_path, traffic_data_path, carbon_intensity_data_path, month_to_analyze, days_in_month)

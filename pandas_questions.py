"""Plotting referendum results in pandas.

In short, we want to make beautiful map to report results of a referendum.
In some way, we would like to depict results with something similar to the
maps that you can find here:
https://github.com/x-datascience-datacamp/datacamp-assignment-pandas/blob/main/example_map.png

To do that, you will load the data as pandas.DataFrame, merge the info and
aggregate them by regions and finally plot them on a map using `geopandas`.
"""
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt


def load_data():
    """Load data from the CSV files referundum/regions/departments."""
    referendum = pd.read_csv('data/referendum.csv', sep=';')
    regions = pd.read_csv('data/regions.csv')
    departments = pd.read_csv('data/departments.csv')

    return referendum, regions, departments


def merge_regions_and_departments(regions, departments):
    """Merge regions and departments in one DataFrame.

    The columns in the final DataFrame should be:
    ['code_reg', 'name_reg', 'code_dep', 'name_dep']
    """
    # Rename columns to match expected output
    regions_renamed = regions.rename(columns={
        'code': 'code_reg',
        'name': 'name_reg'
    })

    departments_renamed = departments.rename(columns={
        'code': 'code_dep',
        'name': 'name_dep',
        'region_code': 'code_reg'
    })

    # Use LEFT join to keep ALL departments, even if region doesn't exist
    merged = departments_renamed.merge(
        regions_renamed,
        on='code_reg',
        how='left'
    )

    result = merged[['code_reg', 'name_reg', 'code_dep', 'name_dep']]

    return result


def merge_referendum_and_areas(referendum, regions_and_departments):
    """Merge referendum and regions_and_departments in one DataFrame.

    You can drop the lines relative to DOM-TOM-COM departments, and the
    french living abroad, which all have a code that contains `Z`.

    DOM-TOM-COM departments are departements that are remote from
    metropolitan France, like Guadaloupe, Reunion, or Tahiti.
    """
    # Add code_dep column to referendum
    referendum = referendum.copy()
    referendum['code_dep'] = referendum['Department code']

    # Filter out departments with 'Z' BEFORE merging
    referendum_filtered = referendum[
        ~referendum['Department code'].str.contains('Z', na=False)
    ].copy()

    # First merge on code_dep
    result = referendum_filtered.merge(
        regions_and_departments,
        on='code_dep',
        how='left'
    )

    # For rows with missing region info, try to match by department name
    missing_mask = result['code_reg'].isna()
    
    if missing_mask.any():
        # Create a secondary merge on department names
        missing_rows = result[missing_mask].copy()
        
        # Try to match by department name
        name_match = missing_rows[['Department name']].merge(
            regions_and_departments.rename(columns={'name_dep': 'Department name'}),
            on='Department name',
            how='left'
        )
        
        # Fill in the missing region information
        result.loc[missing_mask, 'code_reg'] = name_match['code_reg'].values
        result.loc[missing_mask, 'name_reg'] = name_match['name_reg'].values
        result.loc[missing_mask, 'name_dep'] = name_match['Department name'].values

    return result


def compute_referendum_result_by_regions(referendum_and_areas):
    """Return a table with the absolute count for each region.

    The return DataFrame should be indexed by `code_reg` and have columns:
    ['name_reg', 'Registered', 'Abstentions', 'Null', 'Choice A',
    'Choice B']
    """
    # Group by region code and aggregate
    grouped = referendum_and_areas.groupby('code_reg').agg({
        'name_reg': 'first',
        'Registered': 'sum',
        'Abstentions': 'sum',
        'Null': 'sum',
        'Choice A': 'sum',
        'Choice B': 'sum'
    })

    return grouped


def plot_referendum_map(referendum_result_by_regions):
    """Plot a map with the results from the referendum.

    * Load the geographic data with geopandas from `regions.geojson`.
    * Merge these info into `referendum_result_by_regions`.
    * Use the method `GeoDataFrame.plot` to display the result map.
      The results should display the rate of 'Choice A' over all
      expressed ballots.
    * Return a gpd.GeoDataFrame with a column 'ratio' containing
      the results.
    """
    # Load geographic data
    geo_regions = gpd.read_file('data/regions.geojson')

    # Rename code column to match
    geo_regions = geo_regions.rename(columns={'code': 'code_reg'})

    # Calculate ratio of Choice A over expressed ballots
    results_with_ratio = referendum_result_by_regions.copy()
    expressed_ballots = (
        results_with_ratio['Choice A'] + results_with_ratio['Choice B']
    )
    results_with_ratio['ratio'] = (
        results_with_ratio['Choice A'] / expressed_ballots
    )

    # Merge with geographic data
    geo_results = geo_regions.merge(
        results_with_ratio,
        on='code_reg',
        how='left'
    )

    # Plot the map
    fig, ax = plt.subplots(1, 1, figsize=(12, 10))
    geo_results.plot(
        column='ratio',
        cmap='RdYlGn',
        legend=True,
        ax=ax,
        edgecolor='black',
        linewidth=0.5
    )
    ax.set_title(
        'Referendum Results by Region - Choice A Ratio',
        fontsize=16,
        fontweight='bold'
    )
    ax.axis('off')

    return geo_results


if __name__ == "__main__":

    referendum, df_reg, df_dep = load_data()
    regions_and_departments = merge_regions_and_departments(
        df_reg, df_dep
    )
    referendum_and_areas = merge_referendum_and_areas(
        referendum, regions_and_departments
    )
    referendum_results = compute_referendum_result_by_regions(
        referendum_and_areas
    )
    print(referendum_results)

    plot_referendum_map(referendum_results)
    plt.show()

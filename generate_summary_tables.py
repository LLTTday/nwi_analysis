#!/usr/bin/env python3
"""
Script to pre-compute summary tables for the Tables page.
This generates separate CSV files for States, Counties, CSAs, and Cities
instead of calculating them on-the-fly from block group data.
"""

import pandas as pd
import sqlite3
from data_handler import load_data, calculate_weighted_average_nwi_c
import os

def create_summary_table(df, region_type_name, output_filename):
    """Create a summary table for a given region type and save to CSV"""
    print(f"Generating {output_filename}...")
    
    # Mapping NWI levels to human-readable labels
    nwi_to_label_map = {
        0: "1-Least",
        1: "2-Below Avg", 
        2: "3-Above Avg",
        3: "4-Most",
    }

    # Replace NWI numeric levels with labels
    df["nwi_label"] = df["nwi"].map(nwi_to_label_map)

    # Sum populations by region and NWI level
    summed_df = (
        df.groupby([region_type_name, "nwi_label"])["b02001_001e"].sum().reset_index()
    )

    # Pivot to get NWI levels as columns for each region
    pivoted_df = summed_df.pivot(
        index=region_type_name, columns="nwi_label", values="b02001_001e"
    ).reset_index()

    # Calculate weighted average NWI for each region  
    weighted_averages = []
    for region in df[region_type_name].unique():
        if pd.isna(region):
            continue
        region_data = df[df[region_type_name] == region]
        avg_nwi = calculate_weighted_average_nwi_c(
            region_data, nwi_column="nwi_scaled_10", population_column="b02001_001e"
        )
        weighted_averages.append({region_type_name: region, "Avg Walkability Index": avg_nwi})
    
    weighted_averages = pd.DataFrame(weighted_averages)

    # Rename columns to match display format
    cols_rename_map = {
        "1-Least": "1 - Least Walkable",
        "2-Below Avg": "2 - Below Avg",
        "3-Above Avg": "3 - Above Avg", 
        "4-Most": "4 - Most Walkable",
    }
    pivoted_df = pivoted_df.rename(columns=cols_rename_map)

    # Merge with weighted averages
    final_df = pd.merge(pivoted_df, weighted_averages, on=region_type_name)

    # Add ranking
    final_df["Rank"] = final_df["Avg Walkability Index"].rank(method='min', ascending=False).astype(int)

    # Reorder columns to put Rank first
    cols = ["Rank"] + [col for col in final_df.columns if col != "Rank"]
    final_df = final_df[cols]

    # Rename region column to "Name"
    final_df = final_df.rename(columns={region_type_name: "Name"})
    
    # Sort by rank with 1 at the top
    final_df = final_df.sort_values('Rank').reset_index(drop=True)
    
    # Fill NaN values with 0 for population columns
    population_cols = ["1 - Least Walkable", "2 - Below Avg", "3 - Above Avg", "4 - Most Walkable"]
    final_df[population_cols] = final_df[population_cols].fillna(0)
    
    # Save to CSV
    output_path = f"data/{output_filename}"
    final_df.to_csv(output_path, index=False)
    print(f"Saved {len(final_df)} rows to {output_path}")
    
    return final_df

def main():
    """Generate all summary tables"""
    print("Loading block group data...")
    df = load_data()
    
    # Filter to block groups only
    df = df[df['geography_type'] == 'block_group'].copy()
    print(f"Loaded {len(df):,} block group records")
    
    # Create data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)
    
    # Generate States table
    states_df = df[df['state_name'].notna()].copy()
    create_summary_table(states_df, "state_name", "summary_states.csv")
    
    # Generate Counties table  
    counties_df = df[df['county_name'].notna()].copy()
    create_summary_table(counties_df, "county_name", "summary_counties.csv")
    
    # Generate CSAs table
    csa_df = df[df['csa_name'].notna()].copy() 
    create_summary_table(csa_df, "csa_name", "summary_csas.csv")
    
    # Generate Cities table (with city, state format)
    cities_df = df[(df['city_name'].notna()) & (df['state_name'].notna())].copy()
    cities_df['city_state'] = cities_df['city_name'] + ', ' + cities_df['state_name']
    create_summary_table(cities_df, "city_state", "summary_cities.csv")
    
    print("\n✅ All summary tables generated successfully!")
    print("Files created:")
    print("  - data/summary_states.csv")
    print("  - data/summary_counties.csv") 
    print("  - data/summary_csas.csv")
    print("  - data/summary_cities.csv")

if __name__ == "__main__":
    main()
import pandas as pd
from config import field_dict, colors, fields, nwi_labels
import altair as alt
import streamlit as st
import sqlite3
# import pygris

# Remove global connection - use context managers instead


def set_region_type():
    st.session_state.region = None


def set_region(region):
    if not st.session_state.region:
        st.session_state.region = region


# @st.cache_data
def sum_df(x, region_type):
    if region_type == "national":
        x_sum = x.groupby("nwi").sum()
    else:
        x_sum = x.groupby([region_type.lower(), "nwi"]).sum()
    # sum_columns = x_sum.loc[:, x_sum.dtypes != 'object'].columns
    sum_columns = field_dict.values()
    percentage_df = (x_sum.loc[:, sum_columns] / x_sum.loc[:, sum_columns].sum()) * 100
    percentage_df.columns = [f"{col}_pct" for col in percentage_df.columns]
    x_sum = pd.concat([x_sum, percentage_df], axis=1)
    return x_sum


# def subset(region_type, region):
#     if region_type == "national":
#         subset = df
#     else:
#         subset = df[df[region_type.lower()] == region]
#     return subset


# @st.cache_data
def horizontal_stacked(x, column_name, dimension):
    x = x.reset_index()
    x["NWI Level"] = x["NWI Level"].astype(str)
    chart = (
        alt.Chart(x)
        .mark_bar()
        .encode(
            x=alt.X(f"{column_name}:Q", stack="normalize", title=None),
            color=alt.Color("NWI Level:N", scale=alt.Scale(range=colors), legend=None),
        )
        .properties(
            # width=400,
            height=12
        )
    )
    # Create a text mark for the Y-axis label
    text = (
        alt.Chart()
        .mark_text()
        .encode(
            y=alt.Y(
                "NWI Level:N",
                axis=alt.Axis(
                    title=dimension,
                    titleAngle=0,
                    titleAlign="right",
                    titleAnchor="end",
                    orient="left",
                ),
            ),
        )
    )
    charts = alt.layer(
        text,
        chart,
    )
    return charts


@st.cache_data
def group_by_geography(df, fields=fields, region_type="national"):
    fields = fields + region_type.lower() if region_type == "national" else fields
    regions = (
        ["nwi"].append(region_type.lower()) if region_type == "national" else "nwi"
    )
    summed = df.groupby(regions).sum()[fields].reset_index()
    return summed


# @st.cache_data(persist=True)
@st.cache_data
def group_by_region(df, region_type, region):
    cols = [x for x in df.columns if x[0] == "b"]
    
    # Handle city data differently since each city is only one row
    if region_type == "city" and region is not None:
        # For a specific city, just return the single row with NWI level
        if len(df) == 1:
            result = df[["nwi"] + cols].copy()
            return result.reset_index(drop=True)
    
    # Normal groupby for block group data or multiple cities
    summed = df.groupby("nwi")[cols].sum().reset_index()
    return summed


@st.cache_data
def load_data():
    """Load block group data with caching for performance"""
    with sqlite3.connect('data/nwi_full_2019_complete.db') as conn:
        # Load only block group data for city aggregation
        df = pd.read_sql("""
            SELECT * FROM nwi_full 
            WHERE geography_type = 'block_group'
        """, conn)
    return df

@st.cache_data
def get_city_names():
    """Get cached list of available cities from block group data"""
    with sqlite3.connect('data/nwi_full_2019_complete.db') as conn:
        cities = pd.read_sql("""
            SELECT DISTINCT city_name || ', ' || state_name as city_display
            FROM nwi_full 
            WHERE geography_type = 'block_group' 
            AND city_name IS NOT NULL
            ORDER BY city_display
        """, conn)
    return cities['city_display'].tolist()


#@st.cache_data
def get_data(region_type, region, table):
    if region_type.lower() == "national":
        # For national view, use block group data only
        st.session_state.subset = table[table['geography_type'] == 'block_group']
    elif region_type.lower() == "city":
        if region is not None:
            # Parse "City, State" format
            if ", " in region:
                city_name, state_name = region.split(", ", 1)
            else:
                city_name = region
                state_name = None
            
            # For specific city, use block groups within that city
            if state_name:
                city_bgs = table[
                    (table['geography_type'] == 'block_group') & 
                    (table['city_name'] == city_name) &
                    (table['state_name'] == state_name)
                ]
            else:
                city_bgs = table[
                    (table['geography_type'] == 'block_group') & 
                    (table['city_name'] == city_name)
                ]
            
            if len(city_bgs) == 0:
                st.error(f"No block groups found for city: {region}")
                return
            st.session_state.subset = city_bgs
        else:
            # For city selection, show all block groups that have cities
            st.session_state.subset = table[
                (table['geography_type'] == 'block_group') & 
                (table['city_name'].notna())
            ]
    else:
        # For other region types (state, county, csa), use block group data
        region_type_label = region_type.lower() + "_name"
        if region is not None:
            df = table[
                (table['geography_type'] == 'block_group') & 
                (table[region_type_label] == region)
            ]
            st.session_state.subset = df
        else:
            st.session_state.subset = table[table['geography_type'] == 'block_group']
    
    st.session_state.subset = st.session_state.subset.copy()
    st.session_state.subset["NWI Level"] = st.session_state.subset["nwi"].map(
        {0: 1, 1: 2, 2: 3, 3: 4}
    )
    update_population()
    make_pop_chart()


def update_population():
    st.session_state.nwi_population = group_by_region(
        st.session_state.subset,
        st.session_state.region_type.lower(),
        st.session_state.region,
    )
    st.session_state.nwi_population["NWI Level"] = pd.Categorical(st.session_state.nwi_population[
        "nwi"
    ].map(
        {
            0: "1 - Least Walkable",
            1: "2 - Below Average",
            2: "3 - Above Average",
            3: "4 - Most Walkable",
        }
    ))
    st.session_state.nwi_population = st.session_state.nwi_population.rename(
        columns={"b02001_001e": "Population"}
    )


def make_pop_chart():
    # Ensure Population column is numeric
    st.session_state.nwi_population['Population'] = pd.to_numeric(st.session_state.nwi_population['Population'], errors='coerce').fillna(0)
    st.session_state.nwi_population['Percent'] = (st.session_state.nwi_population['Population'] / st.session_state.nwi_population['Population'].sum())
    chart = (
        alt.Chart(st.session_state.nwi_population)
        .mark_bar()
        .encode(
            x=alt.X("Population:Q", axis=alt.Axis(labels=False), title=""),
            y=alt.Y(
                "NWI Level:N"
            ),  # This sorts the bars based on the values of x
            color=alt.Color("NWI Level:N", scale=alt.Scale(range=colors), legend=None),
            tooltip=["NWI Level", "Population", alt.Tooltip("Percent", format=".1%"), alt.Tooltip("Population", format=",")]
        )
        .properties(width=600, height=400, title="Total Population by NWI Level")
    )

    text = alt.Chart(st.session_state.nwi_population).mark_text(
            align='left',
            baseline='middle',
            color="grey",
            fontStyle='bold',
            fontSize=14,
            dx=5  # Adjust the distance of the label from the bar
        ).encode(
            x=alt.X('sum(Population):Q'),
                    y='NWI Level:N',
                    text=alt.Text("Percent", format='.1%')
        )
    st.session_state.pop_chart = chart + text

    return st.session_state.pop_chart


def demo_viz_b(demographic):
    # This now fetches a dictionary of categories and their corresponding column names for the selected demographic
    demo_dict = field_dict[demographic]

    charts = []

    # Assuming you want a separate chart for each category within the demographic
    for category, column_name in demo_dict.items():
        # Prepare data for the current category - need to convert TEXT to numeric and group by NWI Level
        # Get the data and convert the column to numeric
        df = st.session_state.subset.copy()
        df[column_name.lower()] = pd.to_numeric(df[column_name.lower()], errors='coerce').fillna(0)
        
        # Group by NWI Level and sum the demographic column
        chart_data = df.groupby("NWI Level")[column_name.lower()].sum().reset_index()
        
        # Assuming horizontal_stacked can take this filtered DataFrame and generate a chart
        c = horizontal_stacked(
            chart_data,
            column_name.lower(),  # The column to stack on the x-axis
            category,  # Passing the category name for labeling purposes
        )
        charts.append(c)

    # Assuming you'd like to vertically concatenate all generated charts for each category
    all_charts = alt.vconcat(*charts, spacing=20).resolve_scale(x="independent")
    st.altair_chart(all_charts, use_container_width=True)


def demo_viz_c(demographic):
    # Assuming NWI levels are numerically ordered 1 through 4
    nwi_levels = range(1, 5)
    charts = []

    # Iterate through each NWI level
    for level in nwi_levels:
        # Filter data for the current NWI level
        level_data = st.session_state.subset[
            st.session_state.subset["NWI Level"] == level
        ]

        # Prepare data for the chart: for each category in the demographic, sum the population
        category_sums = []
        for category, column_name in field_dict[demographic].items():
            # Assuming each column represents a population count, summing up for the current level.
            # Adjust if your data aggregation logic differs.
            category_sum = level_data[column_name.lower()].sum()
            category_sums.append({"Category": category, "Total": category_sum})

        # Convert aggregated data to DataFrame
        df_chart = pd.DataFrame(category_sums)

        # Generate chart for this NWI level
        chart = (
            alt.Chart(df_chart)
            .mark_bar()
            .encode(
                x="Total:Q",
                y=alt.Y(
                    "Category:N", sort="-x"
                ),  # Sorting categories based on total, descending
                color=alt.value("steelblue"),  # You can customize this as needed
                tooltip=["Category:N", "Total:Q"],
            )
            .properties(
                title=f"NWI Level {level} Population by {demographic}",
                width=600,
                height=200,  # Adjust height as needed based on number of categories
            )
        )

        charts.append(chart)

    # Combining all charts vertically
    combined = alt.vconcat(*charts, spacing=20)
    st.altair_chart(combined, use_container_width=True)


def demo_viz_a(demographic):
    demo_dict = field_dict[demographic]
    charts = []
    for key, value in demo_dict.items():
        c = horizontal_stacked(
            st.session_state.subset.loc[:, [value.lower(), "NWI Level"]],
            value.lower(),
            key,
        )
        charts.append(c)
    st.altair_chart(alt.vconcat(*charts, spacing=45), use_container_width=True)


@st.cache_data
def show_totals(df, region_type):
    summed_df = group_by_geography(df, region_type=region_type)
    chart = horizontal_stacked(summed_df, "B02001_001E", "Population")
    return summed_df, chart


@st.cache_data
def region_totals(df, region_type, region):
    if region_type.lower() != "national" and region is not None:
        df = df.groupby("nwi")["b02001_001e"].sum().reset_index()


def calculate_weighted_average_nwi():
    # Use 'nwi_scaled_10' for the NWI ratings (1-10 scale) and 'b02001_001e' for the population counts
    nwi_column = "nwi_scaled_10"
    population_column = "b02001_001e"

    # DataFrame for calculation
    df = st.session_state.subset.copy()

    # Ensure the relevant data are numeric
    df[nwi_column] = pd.to_numeric(df[nwi_column], errors="coerce")
    df[population_column] = pd.to_numeric(df[population_column], errors="coerce")

    # Calculate the weighted sum of NWI ratings
    weighted_nwi_sum = (df[nwi_column] * df[population_column]).sum()

    # Calculate the total population
    total_population = df[population_column].sum()

    # Protect against division by zero if there's no population data
    if total_population > 0:
        weighted_average_nwi = weighted_nwi_sum / total_population
        return weighted_average_nwi
    else:
        # Return a placeholder or default value (e.g., 0) if total_population is zero
        return 0


# @st.cache_data
# def get_geography(region_type, region):
#     if region_type.lower() == 'national' or region is None:
#         pass
#     if region_type.lower() == 'county':
#         geo = pygris.block_groups(county=region, year=2010)
#     else:
#         pass


def prepare_grouped_df(region_type_name):
    # Assuming 'st.session_state.subset' holds the DataFrame
    df = st.session_state.subset

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
        region_data = df[df[region_type_name] == region]
        avg_nwi = calculate_weighted_average_nwi_c(
            region_data, nwi_column="nwi_scaled_10", population_column="b02001_001e"
        )
        weighted_averages.append({region_type_name: region, "Avg Walkability Index": avg_nwi})
    
    weighted_averages = pd.DataFrame(weighted_averages)

    # Rename columns to match 'nwi_to_label_map' values directly if needed
    cols_rename_map = {
        "0": "1 - Least Walkable",
        "1": "2 - Below Avg",
        "2": "3 - Above Avg",
        "3": "4 - Most Walkable",
    }
    pivoted_df = pivoted_df.rename(columns=cols_rename_map)

    final_df = pd.merge(pivoted_df, weighted_averages, on=region_type_name)

    ins_col = final_df["Avg Walkability Index"].rank(method='min', ascending=False).astype(int)

    final_df.insert(0,"Rank",ins_col)

    final_df = final_df.rename(columns=lambda x: 'Name' if '_name' in x else x)
    
    # Sort by rank with 1 at the top
    final_df = final_df.sort_values('Rank').reset_index(drop=True)

    return final_df


def calculate_weighted_average_nwi_b(
    df, nwi_column="nwi", population_column="b02001_001e"
):
    if df.empty:
        return 0

    df[nwi_column] = pd.to_numeric(df[nwi_column], errors="coerce")
    df[population_column] = pd.to_numeric(df[population_column], errors="coerce")

    weighted_nwi_sum = (df[nwi_column] * df[population_column]).sum()
    total_population = df[population_column].sum()

    if total_population > 0:
        return weighted_nwi_sum / total_population
    else:
        return 0


def calculate_weighted_average_nwi_c(df, nwi_column, population_column):
    if df.empty:
        return 0

    # Always use nwi_scaled_10 for 1-10 scale
    nwi_column = "nwi_scaled_10"
    nwi_values = pd.to_numeric(df[nwi_column], errors="coerce")
    populations = pd.to_numeric(df[population_column], errors="coerce")

    weighted_nwi_sum = (nwi_values * populations).sum()
    total_population = populations.sum()

    return weighted_nwi_sum / total_population if total_population > 0 else 0


@st.cache_data
def demo_scatter_plot(demographic, selected_metric=None):
    """Create scatter plot of demographic percentages vs NWI scores for each block group"""
    df = st.session_state.subset.copy()
    
    # Get demographic categories
    demo_dict = field_dict[demographic]
    
    # Use selected metric or default to first
    if selected_metric and selected_metric in demo_dict:
        category = selected_metric
    else:
        category = list(demo_dict.keys())[0]
    
    demo_column = demo_dict[category].lower()
    
    # Ensure numeric data types - use nwi_scaled_10 for 1-10 scale
    df[demo_column] = pd.to_numeric(df[demo_column], errors='coerce').fillna(0)
    df['nwi_scaled_10'] = pd.to_numeric(df['nwi_scaled_10'], errors='coerce').fillna(0)
    df['b02001_001e'] = pd.to_numeric(df['b02001_001e'], errors='coerce').fillna(0)
    
    # Calculate percentage for the demographic category
    df['demo_percentage'] = (df[demo_column] / df['b02001_001e'] * 100).fillna(0)
    
    # Filter out block groups with zero population
    df_filtered = df[df['b02001_001e'] > 0].copy()
    
    if len(df_filtered) == 0:
        st.warning("No data available for scatter plot")
        return
    
    # Optimize for large datasets - sample if > 5000 points
    if len(df_filtered) > 5000:
        df_filtered = df_filtered.sample(n=5000, random_state=42)
        st.info(f"Showing sample of 5,000 block groups (out of {len(df)} total)")
    
    # Adjust point size based on dataset size
    point_size = max(20, min(60, 5000 / len(df_filtered)))
    
    # Create scatter plot
    scatter = (
        alt.Chart(df_filtered)
        .mark_circle(size=point_size, opacity=0.6)
        .encode(
            x=alt.X('demo_percentage:Q', 
                   title=f'{category} Percentage',
                   scale=alt.Scale(domain=[0, 100])),
            y=alt.Y('nwi_scaled_10:Q', 
                   title='National Walkability Index Score (1-10)',
                   scale=alt.Scale(domain=[1, 10])),
            color=alt.Color('NWI Level:N', 
                          scale=alt.Scale(range=colors),
                          legend=alt.Legend(title="NWI Level")),
            tooltip=[
                alt.Tooltip('geoid10:N', title='Block Group ID'),
                alt.Tooltip('demo_percentage:Q', title=f'{category} %', format='.1f'),
                alt.Tooltip('nwi_scaled_10:Q', title='NWI Score (1-10)', format='.1f'),
                alt.Tooltip('NWI Level:N', title='NWI Level'),
                alt.Tooltip('b02001_001e:Q', title='Population', format=',')
            ]
        )
        .properties(
            title=f'{category} Percentage vs NWI Score by Block Group',
            width=700,
            height=400
        )
    )
    
    st.altair_chart(scatter, use_container_width=True)


def demo_viz_d(demographic):
    # Assuming NWI levels are numerically ordered 1 through 4
    nwi_levels = range(1, 5)
    charts = []

    # Iterate through each NWI level
    for level in nwi_levels:
        # Filter data for the current NWI level
        level_data = st.session_state.subset[
            st.session_state.subset["NWI Level"] == level
        ].copy()

        # Prepare data for the chart: for each category in the demographic, sum the population
        category_data = []
        total_population = 0
        for category, column_name in field_dict[demographic].items():
            # Convert TEXT to numeric before summing
            level_data[column_name.lower()] = pd.to_numeric(level_data[column_name.lower()], errors='coerce').fillna(0)
            # Summing up for the current level for each category
            category_sum = level_data[column_name.lower()].sum()
            category_data.append({"Category": category, "Population": category_sum})
            total_population += category_sum

        # Now calculate the percentage for each category relative to the total population of this level
        for item in category_data:
            item["Percentage"] = (
                (item["Population"] / total_population) * 100
                if total_population > 0
                else 0
            )

        # Convert aggregated data to DataFrame
        df_chart = pd.DataFrame(category_data)

        # Generate chart for this NWI level with normalized bars
        chart = (
            alt.Chart(df_chart)
            .mark_bar()
            .encode(
                x=alt.X(
                    "Percentage:Q",
                    axis=alt.Axis(format=".2f"),
                    title="Percentage of Total",
                ),
                y=alt.Y(
                    "Category:N", sort="-x"
                ),  # Sorting categories based on percentage, descending
                color=alt.value("steelblue"),  # You can customize colors as needed
                tooltip=[
                    alt.Tooltip("Category:N", title="Category"),
                    alt.Tooltip("Population:Q", title="Population"),
                    alt.Tooltip("Percentage:Q", title="Percentage", format=".2f"),
                ],
            )
            .properties(
                title=f"NWI Level {level} - Population Percentage by {demographic}",
                width=600,
                height=200,
            )
        )

        charts.append(chart)

    # Combining all charts vertically
    combined = alt.vconcat(*charts, spacing=20)
    st.altair_chart(combined, use_container_width=True)

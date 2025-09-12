import streamlit as st
import pandas as pd
import numpy as np
from config import demo_cats
from data_handler import (
    get_data,
    load_data,
    make_pop_chart,
    update_population,
    demo_viz_b,
    demo_viz_d,
    demo_scatter_plot,
    calculate_weighted_average_nwi,
    prepare_grouped_df,
)

# ----------- Session State Initialization (fixes infinite loop) -----------
if "region_type" not in st.session_state:
    st.session_state.region_type = "national"
if "region" not in st.session_state:
    st.session_state.region = None
if "table" not in st.session_state:
    with st.spinner("Loading data..."):
        st.session_state.table = load_data()
if "subset" not in st.session_state:
    st.session_state.subset = st.session_state.table
if "demo_viz" not in st.session_state:
    st.session_state.demo_viz = "a"
# --------------------------------------------------------------------------

with st.sidebar:
    st.image('AW_logo_horizontal_full_color.png')
    st.markdown(
        "### Walkable Land Use Analysis",
    )
    page = st.sidebar.selectbox("Choose a page", ["Main Page", "Tables"])
    st.markdown(
        "##### Data Sources:\n- [American Community Survey]("
        "https://www.census.gov/data/developers/data-sets/acs-5year.html)  \n *A U.S. Census survey that provides information on a yearly basis about our nation and its people*\n- [National Walkability Index]("
        "https://www.epa.gov/smartgrowth/smart-location-mapping)  \n *A resource of the EPA that ranks U.S. Census block groups according to their relative walkability.*"
    )
    st.markdown(
        "The *population-weighted mean walkable land use* in this tool is based on the data from the EPA's National Walkability Index. It combines different factors that affect how walkable a Census Block Group is--intersection density, transit stop proximity, and diversity of land use--and scores them on a scale from 1 to 20. We calculated the average walkability for various regions and places by adjusting for each block group's population and converted that figure to a 10 point scale. This gave us the average walkability index shown in our tables and plots."
    )
    st.markdown(
        "We use the phrase *Walkable Land Use* because EPA\'s National Walkability Index primarily relies upon density, diversity of land uses, and proximity to transit, which research demonstrates that people located in census blocks with these features walk more. Due to current data limitation it does not measure sidewalks, disability accessibility, shade or street level amenities. See its methodology."
    )
    st.markdown(
        "The latest iteration of the National Walkability Index was published in 2021, using a variety of data sources published between 2017 and 2020. For the demographic estimates used in this analysis, we used the American Community Survey’s five-year estimates for 2015-2019. These are the latest data compatible with the geographies used by the National Walkability Index."
    )

if page == "Main Page":

    # Calculate NWI levels based on natwalkind if nwi is null
    if st.session_state.table["nwi"].isnull().all():
        quantiles = st.session_state.table["natwalkind"].quantile([0.25, 0.5, 0.75])
        conditions = [
            st.session_state.table["natwalkind"] <= quantiles[0.25],
            (st.session_state.table["natwalkind"] > quantiles[0.25]) & (st.session_state.table["natwalkind"] <= quantiles[0.5]),
            (st.session_state.table["natwalkind"] > quantiles[0.5]) & (st.session_state.table["natwalkind"] <= quantiles[0.75]),
            st.session_state.table["natwalkind"] > quantiles[0.75]
        ]
        choices = [0, 1, 2, 3]
        st.session_state.table["nwi"] = np.select(conditions, choices, default=3)
    else:
        st.session_state.table["nwi"] = st.session_state.table["nwi"].fillna(3)

    update_population()
    make_pop_chart()

    st.title("Walkable Land Use by Region, Population, and Demographics")

    st.session_state.region_type = st.selectbox(
        "Select Regional Grouping", ["National", "State", "County", "CSA", "City"]
    )

    if (
        st.session_state.region_type
        and st.session_state.region_type.lower() != "national"
    ):
        if st.session_state.region_type.lower() == "city":
            from data_handler import get_city_names
            names = get_city_names()
        else:
            region_col = st.session_state.region_type.lower() + "_name"
            block_group_table = st.session_state.table[st.session_state.table['geography_type'] == 'block_group']
            names = sorted(block_group_table[region_col].dropna().unique())
        st.session_state.region = st.selectbox("Select Region", names, index=None)

    if st.session_state.region_type is not None and (
        st.session_state.region_type.lower() == "national"
        or (
            st.session_state.region_type.lower() != "national"
            and st.session_state.region is not None
        )
    ):
        get_data(
            st.session_state.region_type,
            st.session_state.region,
            st.session_state.table,
        )
        weighted_average_nwi = calculate_weighted_average_nwi()
        st.metric(label="Population-Weighted Mean Walkable Land Use", value=round(weighted_average_nwi, 1))
        st.altair_chart(st.session_state.pop_chart, use_container_width=True)
        demographic = st.selectbox(
            "Show totals by",
            demo_cats.keys(),
            index=None,
        )
        with st.container():
            if demographic:
                st.write(demo_cats[demographic])
                
                st.subheader("Block Group Analysis")
                from config import field_dict
                metric_options = list(field_dict[demographic].keys())
                selected_metric = st.selectbox(
                    "Select metric to plot:",
                    metric_options,
                    key=f"scatter_metric_{demographic}_{st.session_state.region_type}_{st.session_state.region}"
                )
                demo_scatter_plot(demographic, selected_metric)
                
                st.subheader("Aggregate Analysis")
                chart_type = st.radio(
                    "Chart type",
                    [
                        "Walkable Land Use by Demographic", 
                        "Demographic by Walkable Land Use",
                    ],
                    key=f"chart_type_{demographic}_{st.session_state.region_type}_{st.session_state.region}"
                )
                if chart_type == "Walkable Land Use by Demographic":
                    demo_viz_b(demographic)
                elif chart_type == "Demographic by Walkable Land Use":
                    demo_viz_d(demographic)
    pass
elif page == "Tables":
    region_type_selected = st.selectbox(
        "Select Region Type", options=["State", "County", "CSA", "City"]
    )

    state_filter = None
    if region_type_selected.lower() in ["county", "city"]:
        available_states = sorted(st.session_state.table[
            (st.session_state.table['geography_type'] == 'block_group') &
            (st.session_state.table['state_name'].notna())
        ]['state_name'].unique())
        plural_name = "counties" if region_type_selected.lower() == "county" else "cities"
        state_filter = st.selectbox(
            f"Filter {plural_name} by state (optional):",
            ["All States"] + available_states,
            index=0
        )
        if state_filter == "All States":
            state_filter = None

    region_lower = region_type_selected.lower()
    if region_lower == "county":
        plural_name = "counties"
    elif region_lower == "city":
        plural_name = "cities"
    else:
        plural_name = f"{region_lower}s"
    
    summary_filename = f"data/summary_{plural_name}.csv"
    
    try:
        prepared_df = pd.read_csv(summary_filename)
        if state_filter is not None and region_type_selected.lower() in ["county", "city"]:
            if region_type_selected.lower() == "city":
                prepared_df = prepared_df[prepared_df['Name'].str.endswith(f', {state_filter}')]
            else:
                block_data = st.session_state.table[st.session_state.table['geography_type'] == 'block_group']
                county_state_map = block_data[['county_name', 'state_name']].drop_duplicates()
                county_state_map = dict(zip(county_state_map['county_name'], county_state_map['state_name']))
                prepared_df = prepared_df[
                    prepared_df['Name'].map(county_state_map) == state_filter
                ].copy()
    except FileNotFoundError:
        st.error(f"Summary table {summary_filename} not found. Please run generate_summary_tables.py first.")
        prepared_df = pd.DataFrame()

    st.dataframe(prepared_df, hide_index=True, use_container_width
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

# df.rename(columns={'CSA': 'csa'}, inplace=True)

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
        "We use the phrase “Walkable Land Use” analysis because EPA’s National Walkability Index primarily relies upon density, diversity of land uses, and proximity to transit, which research demonstrates that people located in census blocks with these features walk more. Due to current data limitation it does not measure sidewalks, disability accessibility, shade or street level amenities. See its methodology."
    )
    st.markdown(
        "The latest iteration of the National Walkability Index was published in 2021, using a variety of data sources published between 2017 and 2020. For the demographic estimates used in this analysis, we used the American Community Survey’s five-year estimates for 2015-2019. These are the latest data compatible with the geographies used by the National Walkability Index."
    )


if page == "Main Page":

    if "region_type" not in st.session_state:
        st.session_state.region_type = "national"

    if "region" not in st.session_state:
        st.session_state.region = None

    if "table" not in st.session_state:
        with st.spinner("Loading data..."):
            st.session_state.table = load_data()

    # Calculate NWI levels based on natwalkind if nwi is null
    # NWI levels are typically 0-3, with 3 being most walkable
    # natwalkind is a continuous score, so we need to bin it
    if st.session_state.table["nwi"].isnull().all():
        # Calculate quartiles of natwalkind to create 4 NWI levels
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

    if "subset" not in st.session_state:
        st.session_state.subset = st.session_state.table

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
            # For cities, get city names from cached function
            from data_handler import get_city_names
            names = get_city_names()
        else:
            # For other region types, use block group data
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
                if "demo_viz" not in st.session_state:
                    st.session_state.demo_viz = "a"
                st.write(demo_cats[demographic])
                
                # Add scatter plot above the bar charts
                st.subheader("Block Group Analysis")
                
                # Add metric selection for scatter plot
                from config import field_dict
                metric_options = list(field_dict[demographic].keys())
                selected_metric = st.selectbox(
                    "Select metric to plot:",
                    metric_options,
                    key=f"scatter_metric_{demographic}"
                )
                
                demo_scatter_plot(demographic, selected_metric)
                
                st.subheader("Aggregate Analysis")
                st.session_state.demo_viz = st.radio(
                    "Chart type",
                    [
                        "Walkable Land Use by Demographic",
                        "Demographic by Walkable Land Use",
                    ],
                )
                if st.session_state.demo_viz == "Walkable Land Use by Demographic":
                    demo_viz_b(demographic)
                if st.session_state.demo_viz == "Demographic by Walkable Land Use":
                    demo_viz_d(demographic)
    pass
elif page == "Tables":
    # Initialize session state data if not already done
    if "table" not in st.session_state:
        with st.spinner("Loading data..."):
            st.session_state.table = load_data()
    
    if "subset" not in st.session_state:
        st.session_state.subset = st.session_state.table
    
    region_type_selected = st.selectbox(
        "Select Region Type", options=["State", "County", "CSA", "City"]
    )

    # This is a simplistic representation.
    # You might need to derive `region_type_name` based on `region_type_selected` mapping
    if region_type_selected.lower() == "city":
        # For cities, we need to group by both city_name and state_name
        # Filter to only block groups that have city data
        city_subset = st.session_state.table[
            (st.session_state.table['geography_type'] == 'block_group') & 
            (st.session_state.table['city_name'].notna())
        ]
        st.session_state.subset = city_subset
        # Create a combined city identifier for grouping
        st.session_state.subset = st.session_state.subset.copy()
        st.session_state.subset['city_state'] = st.session_state.subset['city_name'] + ', ' + st.session_state.subset['state_name']
        region_type_name = "city_state"
    else:
        region_type_name = region_type_selected.lower() + "_name"

    prepared_df = prepare_grouped_df(region_type_name)

    # Displaying the DataFrame in Streamlit
    st.dataframe(prepared_df, hide_index=True, use_container_width=True)

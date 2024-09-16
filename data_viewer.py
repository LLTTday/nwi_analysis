import streamlit as st
from config import demo_cats
from data_handler import (
    get_data,
    load_data,
    make_pop_chart,
    update_population,
    demo_viz_b,
    demo_viz_d,
    calculate_weighted_average_nwi,
    prepare_grouped_df,
)

# df.rename(columns={'CSA': 'csa'}, inplace=True)

with st.sidebar:
    page = st.sidebar.selectbox("Choose a page", ["Main Page", "Tables"])
    st.markdown(
        "### Walkable Land Use Analysis *(for America Walks)*",
    )
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
        st.session_state.table = load_data()

    st.session_state.table["nwi"].fillna(3, inplace=True)

    if "subset" not in st.session_state:
        st.session_state.subset = st.session_state.table

    update_population()
    make_pop_chart()

    st.session_state.region_type = st.selectbox(
        "Select Regional Grouping", ["National", "State", "County", "CSA"]
    )

    if (
        st.session_state.region_type
        and st.session_state.region_type.lower() != "national"
    ):
        region_col = st.session_state.region_type.lower() + "_name"
        names = sorted(st.session_state.table[region_col].dropna().unique())
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
        st.markdown(
            f"**Weighted Average of Walkable Land Use for {st.session_state.region if st.session_state.region else 'the Selected Region'}:** `{weighted_average_nwi:.2f}`"
        )
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
    region_type_selected = st.selectbox(
        "Select Region Type", options=["State", "County", "CSA"]
    )

    # This is a simplistic representation.
    # You might need to derive `region_type_name` based on `region_type_selected` mapping
    region_type_name = region_type_selected.lower() + "_name"

    prepared_df = prepare_grouped_df(region_type_name)

    # Displaying the DataFrame in Streamlit
    st.dataframe(prepared_df)

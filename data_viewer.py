import streamlit as st
from config import field_dict
from data_handler import get_data, load_data, make_pop_chart, update_population, horizontal_stacked
import altair as alt

# df.rename(columns={'CSA': 'csa'}, inplace=True)

with st.sidebar:
    st.markdown('### National Walkability Index Analysis *(for America Walks)*', )
    st.markdown(
        '##### Data Sources:\n- [American Community Survey]('
        'https://www.census.gov/data/developers/data-sets/acs-5year.html)  \n- [National Walkability Index]('
        'https://www.epa.gov/smartgrowth/smart-location-mapping)')

if 'region_type' not in st.session_state:
    st.session_state.region_type = 'national'

if 'region' not in st.session_state:
    st.session_state.region = None

if 'table' not in st.session_state:
    st.session_state.table = load_data()

st.session_state.table['nwi'].fillna(3, inplace=True)

if 'subset' not in st.session_state:
    st.session_state.subset = st.session_state.table

update_population()
make_pop_chart()

st.session_state.region_type = st.selectbox('Select Regional Grouping',
                                            ['National', 'State', 'County', 'CSA'])

if st.session_state.region_type and st.session_state.region_type.lower() != 'national':
    region_col = st.session_state.region_type.lower() + '_name'
    names = sorted(st.session_state.table[region_col].dropna().unique())
    st.session_state.region = st.selectbox('Select Region',
                                           names,
                                           index=None)

if st.session_state.region_type is not None and (st.session_state.region_type.lower() == 'national' or (
        st.session_state.region_type.lower() != 'national' and st.session_state.region is not None)):
    get_data(st.session_state.region_type, st.session_state.region, st.session_state.table)
    st.altair_chart(st.session_state.pop_chart, use_container_width=True)
    demographic = st.selectbox('Show totals by',
                               ['Age', 'Race', 'Ethnicity', 'Income', 'Education', 'Homeownership', 'Transportation',],
                               index=None)
    if demographic:
        demo_dict = field_dict[demographic]
        charts = []
        for key, value in demo_dict.items():
            c = horizontal_stacked(st.session_state.subset.loc[:, [value.lower(), 'NWI Level']], value.lower(), key)
            charts.append(c)
        st.altair_chart(alt.vconcat(*charts, spacing=45), use_container_width=True)

#     # Display a map if the region type is 'County' or 'CSA'
#       if st.session_state.region_type.lower() in ['county', 'csa']:
#     # Create a map centered around the selected region
#     # You'll need to replace 'latitude' and 'longitude' with the actual column names in your DataFrame
#     m = folium.Map(location=[st.session_state.table.loc[st.session_state.table[
#                                                             st.session_state.region_type.lower()] == st.session_state.region, 'latitude'].mean(),
#                              st.session_state.table.loc[st.session_state.table[
#                                                             st.session_state.region_type.lower()] == st.session_state.region, 'longitude'].mean()])
# 
#     # Display the map in the Streamlit app
#     folium_static(m)

import pandas as pd
from config import field_dict, colors, fields
import altair as alt
import streamlit as st
import sqlite3
# import pygris

conn = sqlite3.connect('data/nwi_full.db')


def set_region_type():
    st.session_state.region = None


def set_region(region):
    if not st.session_state.region:
        st.session_state.region = region


# @st.cache_data
def sum_df(x, region_type):
    if region_type == 'national':
        x_sum = x.groupby('nwi').sum()
    else:
        x_sum = x.groupby([region_type.lower(), 'nwi']).sum()
    # sum_columns = x_sum.loc[:, x_sum.dtypes != 'object'].columns
    sum_columns = field_dict.values()
    percentage_df = (x_sum.loc[:, sum_columns] / x_sum.loc[:, sum_columns].sum()) * 100
    percentage_df.columns = [f'{col}_pct' for col in percentage_df.columns]
    x_sum = pd.concat([x_sum, percentage_df], axis=1)
    return x_sum


def subset(region_type, region):
    if region_type == 'national':
        subset = df
    else:
        subset = df[df[region_type.lower()] == region]
    return subset


# @st.cache_data
def horizontal_stacked(x, column_name, dimension):
    x = x.reset_index()
    x['NWI Level'] = x['NWI Level'].astype(str)
    chart = alt.Chart(x).mark_bar().encode(
        x=alt.X(f'sum({column_name}):Q', stack='normalize', title=None),
        color=alt.Color('NWI Level:N', scale=alt.Scale(range=colors), legend=None),
    ).properties(
        # width=400,
        height=12
    )
    # Create a text mark for the Y-axis label
    text = alt.Chart().mark_text(
    ).encode(
        y=alt.Y('NWI Level:N', axis=alt.Axis(
            title=dimension,
            titleAngle=0,
            titleAlign='right',
            titleAnchor='end',
            orient='left'
        )
                ),
    )
    charts = alt.layer(text, chart, )
    return charts


@st.cache_data
def group_by_geography(df, fields=fields, region_type='national'):
    fields = fields + region_type.lower() if region_type == 'national' else fields
    regions = ['nwi'].append(region_type.lower()) if region_type == 'national' else 'nwi'
    summed = df.groupby(regions).sum()[fields].reset_index()
    return summed


# @st.cache_data(persist=True)
def group_by_region(df, region_type, region):
    cols = [x for x in df.columns if x[0] == 'b']
    summed = df.groupby('nwi')[cols].sum().reset_index()
    return summed


@st.cache_data(persist=True)
def load_data():
    df = pd.read_sql('SELECT * FROM nwi', conn)
    return df


# @st.cache_data
def get_data(region_type, region, table):
    region_type_label = region_type.lower() + '_name'
    if region_type.lower() != 'national' and region is not None:
        df = table[table[region_type_label] == region]
        st.session_state.subset = df
    else:
        st.session_state.subset = st.session_state.table
    st.session_state.subset['NWI Level'] = st.session_state.subset['nwi'].map(
        {0: 1, 1: 2,
         2: 3, 3: 4})
    update_population()
    make_pop_chart()


def update_population():
    st.session_state.nwi_population = group_by_region(st.session_state.subset, st.session_state.region_type.lower(),
                                                      st.session_state.region)
    st.session_state.nwi_population['NWI Level'] = st.session_state.nwi_population['nwi'].map(
        {0: 'Least Walkable', 1: 'Below Average',
         2: 'Above Average', 3: 'Most Walkable'})
    st.session_state.nwi_population = st.session_state.nwi_population.rename(
        columns={'b02001_001e': 'Population'}).reset_index(drop=True)


def make_pop_chart():
    chart = alt.Chart(st.session_state.nwi_population).mark_bar().encode(
        x='Population:Q',
        y=alt.Y('NWI Level:N', sort=alt.EncodingSortField(field='nwi')),  # This sorts the bars based on the values of x
        tooltip=['NWI Level', 'Population']
    ).properties(
        width=600,
        height=400,
        title='Total Population by NWI Level'
    )
    st.session_state.pop_chart = chart


@st.cache_data
def show_totals(df, region_type):
    summed_df = group_by_geography(df, region_type=region_type)
    chart = horizontal_stacked(summed_df, 'B02001_001E', 'Population')
    return summed_df, chart


@st.cache_data
def region_totals(df, region_type, region):
    if region_type.lower() != 'national' and region is not None:
        df = df.groupby('nwi')['b02001_001e'].sum().reset_index()


# @st.cache_data
# def get_geography(region_type, region):
#     if region_type.lower() == 'national' or region is None:
#         pass
#     if region_type.lower() == 'county':
#         geo = pygris.block_groups(county=region, year=2010)
#     else:
#         pass

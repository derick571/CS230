"""
Name: Derick Babayan
CS230: Section 1
Data: US Cities
URL: Link to your web application on Streamlit Cloud (if posted)

Description: This program creates 2 maps and 2 charts.  It creates a population map that can be filteredd
based on both population as well as state, this map lets you see the population of each city in the state.
There is a density map which allows you to hover over any state and see the density of each one, it also
uses geojson to outline each state.  There is a chart that allows you to see the total population in each time zone,
and there is a chart that lets you see the population in each state filtered on east vs west coast.
"""
import streamlit as st
import pandas as pd
import pydeck as pdk
import matplotlib.pyplot as plt
import numpy as np
from streamlit_modal import Modal
import folium
import json
from streamlit_folium import folium_static
import urllib.request
from branca.colormap import linear


df = pd.read_csv("uscities.csv")

def state_list():
    stateList = []
    for index, row in df.iterrows():
        if row['state_name'] not in stateList:
            stateList.append(row['state_name'])

    stateList.sort()
    return stateList

def timezone_list():
    timezonelist = []
    timezonelistTest = df['timezone'].tolist()
    for item in timezonelistTest:
        if item not in timezonelist:
            timezonelist.append(item)
    return timezonelist

def lists():
    stateList = []
    for index, row in df.iterrows():
        if row['state_name'] not in stateList:
            stateList.append(row['state_name'])

    stateList.sort()

    timezonelist = []
    timezonelistTest = df['timezone'].tolist()
    for item in timezonelistTest:
        if item not in timezonelist:
            timezonelist.append(item)

    return stateList, timezonelist

def filter(population, state):
    state_list, timezone_list = lists()
    if len(state) == 0:
       state = state_list

    df_filtered = df[(df['state_name'].isin(state))]
    df_filtered = df_filtered[(df_filtered['population'] > population[0]) & (df_filtered['population'] < population[1])]

    return df_filtered

def timezoneFilter(timezone):
    state_list, timezone_list = lists()
    if len(timezone) == 0:
        timezone = timezone_list

    df_filtered = df[(df['timezone'].isin(timezone))]

    return df_filtered

def filterCoast(coast):
    west_coast_states = [
        'Alaska', 'California', 'Hawaii', 'Oregon', 'Washington',
        'Arizona', 'Colorado', 'Idaho', 'Montana', 'Nevada',
        'New Mexico', 'Utah', 'Wyoming', 'Kansas', 'Nebraska',
        'North Dakota', 'Oklahoma', 'South Dakota', 'Texas', 'Louisiana',
        'Arkansas', 'Missouri', 'Iowa', 'Minnesota', 'Illinois'
    ]
    east_coast_states = [
        'Maine', 'New Hampshire', 'Vermont', 'Massachusetts', 'Rhode Island',
        'Connecticut', 'New York', 'New Jersey', 'Pennsylvania', 'Delaware',
        'Maryland', 'Virginia', 'West Virginia', 'North Carolina', 'South Carolina',
        'Georgia', 'Florida', 'Ohio', 'Michigan', 'Indiana',
        'Kentucky', 'Tennessee', 'Alabama', 'Mississippi', 'Louisiana'
    ]

    if coast == "East":
        df_filtered = df[(df['state_name'].isin(east_coast_states))]
    else:
        df_filtered = df[(df['state_name'].isin(west_coast_states))]

    return df_filtered

def capital_list():

    df_capital = pd.read_csv("capitals.csv").filter(['state_name', 'city'])

    merged_df = pd.merge(df, df_capital, on=['state_name', 'city'], how='inner')

    return merged_df



def populationMap(df):
    map_df = df.filter(["city", "state_name", "population", "lat", "lng"])

    stateView = pdk.ViewState(latitude=map_df["lat"].mean(),
                              longitude=map_df["lng"].mean(),
                              zoom=3.5)

    layer = pdk.Layer("ScatterplotLayer",
                       data = map_df,
                       get_position = ["lng", "lat"],
                       opacity=0.7,
                       filled = True,
                       get_radius=1200,
                       pickable=True,
                       get_color = [255,255,255]
                      )
    layer1 = pdk.Layer("ScatterplotLayer",
                       data = map_df,
                       get_position = ["lng", "lat"],
                       filled = True,
                       get_radius=2000,
                       pickable=True,
                       get_color = [0,0,0]
                      )

    icon_layer = pdk.Layer(type="IconLayer",
                           data=capital_list(),
                           get_icon="star",
                           get_size=100000,
                           get_scale=150000,
                           get_position=["longitude", "latitude"],
                           pickable=True,
                           )


    tool_tip={"html": "<b>{city}</b><br />Population: {population}"}

    map = pdk.Deck(map_style="mapbox://styles/mapbox/satellite-streets-v12",
                   initial_view_state=stateView, layers=[layer1, layer, icon_layer], tooltip=tool_tip)

    st.pydeck_chart(map)

def timeZoneChart(zone_df, color = "#F90011"):

    tableTimeZone = pd.pivot_table(zone_df, index=['timezone'], values=['population'], aggfunc=np.sum)
    fig, ax = plt.subplots()
    tableTimeZone.plot(kind = 'barh', ax=ax, color=color, edgecolor='black', linewidth=0.5, legend=False)
    ax.set_title("Population by timezone")
    ax.set_xlabel("Population")
    ax.set_ylabel("Timezone")
    ax.bar_label(ax.containers[0], fmt='%d', label_type='edge')
    ax.margins(x=0.2)
    st.pyplot(fig)

def desntiy_map():
    json_url = 'https://raw.githubusercontent.com/PublicaMundi/MappingAPI/86ac7bcffa2da7924757ccb2f048aa1412154ad2/data/geojson/us-states.json'

    m = folium.Map(location=[37.09, -95.71], tiles='CartoDB positron', name="Density Map",
                   zoom_start=3, attr="my Data")

    with urllib.request.urlopen(json_url) as url:
        data = json.loads(url.read().decode())

    density_data = {}
    for feature in data['features']:
        state_name = feature['properties']['name']
        density = feature['properties'].get('density', 0)
        density_data[state_name] = density

    min_density = min(density_data.values())
    max_density = max(density_data.values())
    color_scale = linear.YlOrRd_04.scale(min_density, max_density)

    def style_function(feature):
        state_name = feature['properties']['name']
        density = density_data.get(state_name, 0)
        return {
            'fillColor': color_scale(density),
            'fillOpacity': 0.7,
            'color': 'black',
            'weight': 1,
            'lineOpacity': 0.1
        }

    folium.GeoJson(
        data,
        name="choropleth",
        style_function=style_function,
        highlight_function=lambda x: {'weight': 3, 'color': 'black'},
        smooth_factor=2.0,
        tooltip=folium.features.GeoJsonTooltip(fields=['name', 'density'], labels=True, sticky=True)
    ).add_to(m)

    color_scale.caption = 'Density'
    m.add_child(color_scale)

    folium_static(m)


def piechart(df_coast):

    colors = ['#ff9999','#66b3ff','#99ff99','#ffcc99','#e6b3b3', '#FFE5B4', '#F5FFFA']
    populationTable = pd.pivot_table(df_coast, index=['state_name'], values=['population'], aggfunc=np.sum)
    #ChatGPT helped with 205-208
    explode = [0] * len(populationTable.index)
    max_population_index = populationTable['population'].idxmax()
    explode_index = populationTable.index.get_loc(max_population_index)
    explode[explode_index] = 0.2

    fig, ax = plt.subplots()
    ax = populationTable['population'].plot(kind='pie', labels=populationTable.index, autopct = '%1.1f%%',startangle = 180, shadow=True, colors = colors, explode=explode, fontsize = 6, labeldistance = 1.1)
    ax.set_ylabel('')
    ax.set_title("Pie Chart of state population by part of country")
    st.pyplot(fig)


def popup():

    #ChatGPT Helped with line 225 and 226
    if 'color' not in st.session_state:
        st.session_state['color'] = "#F90011"

    modal = Modal("Color Picker", key="New popup")
    open_modal = st.sidebar.button("Color Picker")
    if open_modal:
        modal.open()

    if modal.is_open():
        with modal.container():
            st.session_state['color'] = st.color_picker('Pick a color to change the chart', '#00f900')
    return st.session_state['color']

def main():

    st.title("US Cities Data Visualization")
    st.write("Welcome to my CS350 project")
    st.sidebar.title("Navbar")

    st.sidebar.write("Please choose from the following options to filter the population map:")
    state = st.sidebar.multiselect("Choose which states:", state_list())
    population = st.sidebar.slider("Choose population range:", 0, 18972871, (1000000, 15000000))
    populationMap(filter(population, state))

    st.write("View of population by timezone:")
    st.sidebar.write("Please choose from the following options to filter the timezone bar chart: ")
    timezone = st.sidebar.multiselect("Choose a timezone:", timezone_list())
    timeZoneChart(timezoneFilter(timezone),popup())

    st.sidebar.write("Please choose from the following options to filter the population pie chart:")
    st.write("The following is a population pie chart of each state in the USA:")
    coast = st.sidebar.radio(
        "East or West Coast",
        ('East', 'West'))
    if coast == 'East':
        st.write(piechart(filterCoast(coast)))
    elif coast == "West":
        st.write(piechart(filterCoast(coast)))

    st.write("The following is a density map of each state in the USA:")
    desntiy_map()


main()
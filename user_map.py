#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 25 15:48:07 2022

@author: alicebernerslee
"""

# import geopandas as gpd


USE_PYGEOS=1
# import pyproj
from shapely.geometry import Point
from geopy.geocoders import Nominatim
import geopandas as gpd
# pyproj.datadir.set_data_dir('/Users/alicebernerslee/opt/anaconda3/share/proj')


import osmnx as ox
ox.config(use_cache=True, log_console=False)
import networkx as nx

# import matplotlib.pyplot as plt
# import matplotlib.lines as mlines

import streamlit as st
# from streamlit_folium import st_folium
import folium
from pyproj import CRS



def get_lat_lon(address):
    locator = Nominatim(user_agent='myGeocoder')
    location = locator.geocode(address)
    # print(location,location.latitude)
    return location.latitude, location.longitude


def make_point(add_name,lat,lon):

    ### origin and destination
    o = gpd.GeoDataFrame(columns = ['name', 'geometry'], crs = 4326, geometry = 'geometry')
    o.at[0, 'geometry'] = Point(lon, lat)
    o.at[0, 'name'] = add_name
    
    return o


def reformat_orgin_dest(origin, destination, graph_fit, edges_fit):
    #  # Get CRS info UTM
    CRS = edges_fit.crs
    
    #  # Reproject all data
    origin_proj = origin.to_crs(crs=CRS)
    destination_proj = destination.to_crs(crs=CRS)
    
    ## get closest nodes to orig and target
    for _, orig in origin_proj.iterrows():
        closest_origin_node = ox.distance.nearest_nodes(G=graph_fit, X = orig.geometry.x, Y = orig.geometry.y) 
#         print(closest_origin_node in graph_proj)
        
    for _, target in destination_proj.iterrows():
        # Find closest node from the graph → point = (latitude, longitude)
        closest_target_node = ox.distance.nearest_nodes(G = graph_fit, X = target.geometry.x, Y = target.geometry.y) 
#         print(closest_target_node in graph_proj)
    return closest_origin_node, closest_target_node


def get_two_routes(gr1, e1, closest_origin_node, closest_target_node):
    
    gr = ox.project_graph(gr1, to_crs='epsg:4326')
    e = e1.to_crs(CRS('EPSG:4326'))
    
    
    ##### get shortest route and safest route
    route1 = nx.shortest_path(G = gr, 
                            source=closest_origin_node, 
                            target=closest_target_node, weight='length')
    
    route2 = nx.shortest_path(G = gr, 
                            source=closest_origin_node, 
                            target=closest_target_node, weight='cpk2')

    # get the danger of these routes
    dangr = []
    lngth = []
    route1_edges = e.loc[route1]
    # print(route1_edges["length"].describe())
    dangr.append(float(route1_edges["cpk2"].median()))
    lngth.append(float(route1_edges["length"].sum()))
    route2_edges = e.loc[route2]
    # print(route2_edges["length"].describe())
    dangr.append(float(route2_edges["cpk2"].median()))
    lngth.append(float(route2_edges["length"].sum()))
    
    return route1, route2, dangr, lngth


# @st.cache()
def user_plot(input_orig,input_dest,graph_fit,edges_fit2,m,ro):

    if input_orig=='nan' or input_dest=='nan':
        return m
    else:
        ##### get the routes from user input and plot
    
        lat1,lon1 = get_lat_lon(input_orig)
        origin = make_point(input_orig,lat1,lon1)
        # print(origin)
        
        lat2,lon2 = get_lat_lon(input_dest)
        destination = make_point(input_orig,lat2,lon2)
        # print(destination)
    
        # # find two routes from origin to destination
        closest_origin_node, closest_target_node = reformat_orgin_dest(origin, destination, graph_fit, edges_fit2)
        # print('done reformat_origin_dest')
        route1, route2, dangr,lngth = get_two_routes(graph_fit, edges_fit2, closest_origin_node, closest_target_node)
        # print('done get_two_routes')
        
        
        Gc = ox.project_graph(graph_fit, to_crs='epsg:4326')
        if ro=='Fastest':
            m = ox.plot_route_folium(Gc, 
                                     route1, 
                                     color='#3388ff',
                                     opacity=0.7,
                                     tiles='openstreetmap',
                                     tooltip = f'Fastest: {round(dangr[0],2)} crashes/km, {lngth[0]} min',
                                     # popup = f'Fastest: {round(dangr[0],2)} crashes/km, {lngth[0]} min',
                                     ).add_to(m)
        elif ro=='Safest':
            m = ox.plot_route_folium(Gc,
                                     route2,
                                     color='#EE4B2B',
                                     opacity=0.7,
                                     tiles='openstreetmap',
                                     tooltip = f'Safest: {round(dangr[1],2)} crashes/km, {lngth[1]} min',
                                     # popup = f'Safest: {round(dangr[1],2)} crashes/km, {lngth[1]} min',
                                     ).add_to(m)
                
        # Marker class only accepts coordinates in tuple form
        start_latlng = (lat1,lon1)
        end_latlng   = (lat2,lon2)
        start_marker = folium.Marker(location = start_latlng,
                                     popup = input_orig,
                                     tooltip = input_orig,
                                     icon = folium.Icon(color='green')
                                     )
        end_marker = folium.Marker(location = end_latlng,
                                    popup = input_dest,
                                    tooltip = input_dest,
                                    icon = folium.Icon(color='red')
                                    )
        # add the circle marker to the map
        start_marker.add_to(m)
        end_marker.add_to(m)

        if 'dangr' not in st.session_state or st.session_state['dangr']!=dangr:
            print('update this')
            st.session_state['dangr'] = dangr
            st.session_state['lngth'] = lngth
        
        
        print('done user_map')
        
        return m 


def change_map(o,d,g,e):
    st.session_state['o'] = o
    st.session_state['d'] = d
    st.session_state['g'] = g
    st.session_state['e'] = e
    print('changed map')

def default_plot(o,g):
    lat, lon = get_lat_lon(o)
    m = folium.Map((lat,lon),zoom_start=14)
    print('done default')
    return m

def get_m(mdict):
    if (st.session_state['o'],st.session_state['d'],st.session_state['route_option']) in mdict:
        print('retreiving',st.session_state['o'],st.session_state['d'],st.session_state['route_option'])
        return mdict[st.session_state['o'],st.session_state['d'],st.session_state['route_option']]
    else:
        if st.session_state['d'] == 'nan':
            m =  default_plot(st.session_state['o'],st.session_state['g'])
        else:
            m =  user_plot(st.session_state['o'],
                                   st.session_state['d'],
                                   st.session_state['g'],
                                   st.session_state['e'],
                                   st.session_state['m'],
                                   st.session_state['route_option'])
        print('adding',st.session_state['o'],st.session_state['d'],st.session_state['route_option'])       
        mdict[st.session_state['o'],st.session_state['d'],st.session_state['route_option']] = m
        return m
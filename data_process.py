#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 25 15:30:01 2022

@author: alicebernerslee
"""
import osmnx as ox
import numpy as np

import os

import glob
import pandas as pd

USE_PYGEOS=1
import pyproj
import geopandas as gpd
pyproj.datadir.set_data_dir('/Users/alicebernerslee/opt/anaconda3/share/proj')
gpd.show_versions()

from sklearn.model_selection import ShuffleSplit

import streamlit as st


def get_edges_nodes():
    # Specify the name that is used to seach for the data
    place_name = "Somerville, Massachusetts, USA"
    
    # Fetch OSM street network from the location
    graph = ox.graph_from_place(place_name)
    
    # Retrieve nodes and edges
    nodes, edges = ox.graph_to_gdfs(graph)
    
    def fix_maxspeed(sts):
        
        if type(sts) is float:
            return np.nan
        else:        
            return float(sts.split(" ")[0])
        
    
    def fix_width(sts):
        
        if type(sts) is float:
            return np.nan
        else:        
            r = sts.replace(';',' ').replace('\'',' ').split()[0]
            return float(r)
       
    #format edges 
    edges.osmid = edges['osmid'].apply(lambda x: x[0] if type(x) is list else x)
    edges.name = edges['name'].apply(lambda x: x[0] if type(x) is list else x)
    edges.highway = edges['highway'].apply(lambda x: x[0] if type(x) is list else x)
    edges.maxspeed = edges['maxspeed'].apply(lambda x: fix_maxspeed(x[0]) if type(x) is list else fix_maxspeed(x))
    edges.lanes = edges['lanes'].apply(lambda x: float(x[0]) if type(x) is list else float(x))
    edges.width = edges['width'].apply(lambda x: fix_width(x[0]) if type(x) is list else fix_width(x))
    return edges, nodes




#### load crash data
@st.experimental_memo
def get_crash_data():
    path = r'/Users/alicebernerslee/Desktop/capstone_streamlit/data' # use your path
    all_files = glob.glob(os.path.join(path, "*_Details.csv"))
    # dat = pd.concat((pd.read_csv(f) for f in all_files), ignore_index=True)
    # SM = dat['CITY'].isin(['Somerville','SOMERVILLE'])
    # dat = dat[SM]
    
    dat = pd.read_csv(all_files[0],low_memory=False)
    # take only somerville streets from crashes too
    SM = dat['CITY'].isin(['Somerville','SOMERVILLE'])
    dat = dat[SM]
    
    for f in all_files[1:]:
        dat1 = pd.read_csv(f,low_memory=False)
        SM = dat1['CITY'].isin(['Somerville','SOMERVILLE'])
        dat1 = dat1[SM]
        dat = pd.concat([dat,dat1], ignore_index=True)

    
    # make crashes into geoframes
        # https://geopandas.org/en/stable/gallery/create_geopandas_from_pandas.html
    sm_crashes2g = gpd.GeoDataFrame(dat, geometry=gpd.points_from_xy(dat.LON, dat.LAT), crs=4326)
    return sm_crashes2g



@st.cache
def merge_crash_streets(sm_crashes2g, edges):
    # convert both to meters
    crash1 = sm_crashes2g.to_crs(3857)
    streets1 = edges.to_crs(3857)
    # join crashes to streets to assign geo to tem
    crash_streets = crash1.sjoin_nearest(streets1, how="left",distance_col = 'distance_col')
    return crash_streets




### creating the metric: bike crashes per meter (crash_per_m) and bring into edges format
# @st.experimental_memo
@st.cache
def create_crash_per_km(crash_streets):
    # make for bike crashes only column
    isbike1 = crash_streets['NON_MTRST_TYPE_CL'].str.contains('Cyclist',na=False,case=False)
    isbike2 = crash_streets['NON_MTRST_TYPE_DESCR'].str.contains('Cyclist',na=False,case=False)
    # isnotcar = crash_streets['PERS_TYPE'].str.contains('Non-motorist')
    y = isbike1 | isbike2
    
    # insert it
    crash_streets.insert(1,'BIKE_CRASH_NUM',crash_streets['CRASH_NUMB'])
    crash_streets.iloc[~y,1] = np.nan
    
    
    ### Group by osmid and add up how many bike crashes
    # crash_streets['osmid'] = crash_streets['osmid'].astype('str') 
    bcn = crash_streets.groupby('osmid')['BIKE_CRASH_NUM'].nunique()
    #make a new column for that number
    st_num = crash_streets.merge(bcn,how = 'left', copy = False, 
                               on ="osmid")
    
    # #insert a column for the crash_per_km
    st_num.insert(1,'crash_per_km', st_num['BIKE_CRASH_NUM_y']/ (st_num['length']/1000))
    return st_num



# @st.experimental_memo
@st.cache
def get_merged_edges(st_numX,edgesX,categorical_columns,osm_columns_cat,numeric_columns,osm_columns_num):
    # #merge the values back to the edges
    # old way, to do on each u,v,key 
    # new way, do on each osmid
    st_num2 = st_numX[['index_right0','index_right1','index_right2' , "crash_per_km"] + categorical_columns + osm_columns_cat + numeric_columns + osm_columns_num]
    
    column_map = {col: "first" for col in st_num2.columns[3:]}
    column_map['crash_per_km'] = "mean"
    
    st_num_inx = st_numX.groupby(['index_right0','index_right1','index_right2'])['crash_per_km'].mean()
    st_num_inx2 = st_numX.groupby(['index_right0','index_right1','index_right2']).agg(column_map)
    
    st2 = st_num_inx2.merge(st_num_inx, how = 'left',
    #                     on = ['index_right0','index_right1','index_right2'], 
                        right_index = True,
                            left_index = True,validate = '1:1')
    
    # NEED TO MERGE ON THE U,V TO GET crash_per_km
    merged_edges = edgesX.merge(st2,how = 'left', 
                               left_on = ['u','v','key'], 
                               right_on = ['index_right0','index_right1','index_right2'],
                              validate = '1:1',
                              suffixes = ['','_y'])
    merged_edges = merged_edges.rename(columns = {'crash_per_km_y':'crash_per_km'})
    return merged_edges



@st.cache
def make_graph_proj(edges, nodes, merged_edges, test_size = .5):
    graph2 = ox.graph_from_gdfs(nodes,edges)
    
     # Reproject the graph
    graph_proj = ox.project_graph(graph2)
    
    # only use half of the crashes to build out this ?
    edges3 = ox.graph_to_gdfs(graph_proj, nodes=False)
    rs = ShuffleSplit(n_splits=1, test_size=test_size, random_state=0)
    rsx = rs.split(range(len(edges3)))
    # X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=0)
    for rsx1 in rsx:
        to_use = rsx1[0]
        # to_hold = rsx1[1]
    
    
    #add attribute of crash_per_km (from merged_edges)
    for key in graph_proj.edges:
        ind = edges.index==key
        indx = [i for i, x in enumerate(ind) if x]
        if indx in to_use:
            graph_proj.edges[key]['crash_per_km_use'] = float(merged_edges[ind]['crash_per_km'])    
        else:
            graph_proj.edges[key]['crash_per_km_use'] = np.nan   
            
        graph_proj.edges[key]['crash_per_km'] = float(merged_edges[ind]['crash_per_km'])
        
    return graph_proj
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 25 15:43:16 2022

@author: alicebernerslee
"""

import osmnx as ox
import numpy as np


from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.linear_model import Ridge
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split

import streamlit as st
import data_process


def getAdj(G,inList, fullList, n):
#     print(n,inList,fullList)
    if n == 0:
        return fullList
    else:
        outList = []
        
    for nd in G.nbunch_iter(inList):
        for neigh in G[nd]:
            if neigh not in fullList:
                fullList.append(neigh)
                outList.append(neigh)
#                 print(len(outList),outList)

    return getAdj(G, outList, fullList, n-1)




### spread crash_per_km to adjascent edges
@st.cache
def spread_out_crash(graph_proj, a = .9):
    c = 1
    edges3 = ox.graph_to_gdfs(graph_proj, nodes=False)
    nansum = sum(edges3['crash_per_km_use'].isna())
    zerosum = sum(edges3['crash_per_km_use']==0)
    # numnum = sum(edges3['crash_per_km_use']>0)
    while zerosum>100 or nansum>200:
    
        #go through all edges
        for n1,n2,dat in graph_proj.edges.data('crash_per_km_use'):
            
            if dat and dat>0:
    
                nn = getAdj(graph_proj,[n1,n2],[],c)
                adj_edges = graph_proj.edges(nn)  
    
                if 'cpk2' in graph_proj.edges[[n1] + [n2] + [0]]:
                    th2 = graph_proj.edges[[n1] + [n2] + [0]]['cpk2']
                    if not np.isnan(th2):
                        dat += th2
    
                toadddat = a/c * dat
    
                #update them by adding half the crash danger of streets next to them
                for edg in adj_edges:
                    u,v = edg
    
                    th = graph_proj.edges[[u] + [v] + [0]]['crash_per_km_use'] 
    
                    if np.isnan(th):
                        th = 0
    
                    toadd = th + toadddat
    
                    if not np.isnan(toadd):
                        graph_proj.edges[[u] + [v] + [0]]['cpk2'] = toadd
    
        edges3 = ox.graph_to_gdfs(graph_proj, nodes=False)
        nansum = sum(edges3['cpk2'].isna())
        zerosum = sum(edges3['cpk2']==0)
        numnum = sum(edges3['cpk2']>0)
        c += 1
        print(nansum,zerosum, numnum)
        
    return graph_proj, edges3

@st.cache
def merge_new_var_in(edges3, st_num):
    ## merge to get new map into the streets data frame
    new_st_num = edges3.merge(st_num,how = 'right', 
                               left_on = ['u','v','key'], 
                               right_on = ['index_right0','index_right1','index_right2'],
                              validate = '1:m',
                              suffixes = ['','_y'])
    return new_st_num

@st.cache
def make_fit_model(new_st_num,categorical_columns,osm_columns_cat,numeric_columns,osm_columns_num):
    
    #### model
    features = ColumnTransformer([
        ('categorical', OneHotEncoder(handle_unknown = 'ignore'), osm_columns_cat + categorical_columns),
          ('numeric', SimpleImputer(), osm_columns_num + numeric_columns)])
    est = Pipeline([
        ('features', features),
        ('regressor', Ridge(alpha = 1))
    ],verbose = True)
    
    #### fit model
    new_st_num2 = new_st_num[new_st_num['crash_per_km'].notnull()]
    st_num_leaveout = new_st_num2[new_st_num2['crash_per_km_use'].isna()]
    X = st_num_leaveout[osm_columns_cat + osm_columns_num + categorical_columns + numeric_columns]
    y = st_num_leaveout['crash_per_km']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=0)
    est.fit(X_train, y_train)
    # r2 = est.score(X_test, y_test)
    # print(f'Train on 80%, test on 20%: R^2 = {round(r2,3)}')
    return est

@st.cache
def predict_map(new_st_num,edges3,est,categorical_columns,osm_columns_cat,numeric_columns,osm_columns_num):
    
    edges_fit = data_process.get_merged_edges(new_st_num,edges3,categorical_columns,osm_columns_cat,numeric_columns,osm_columns_num)
    
    edges_fit['highway'] = edges_fit['highway'].astype('str') 
    edges_fit['oneway'] = edges_fit['oneway'].astype('str') 
    edges_fit['name'] = edges_fit['name'].astype('str') 
    edges_fit['osmid'] = edges_fit['osmid'].astype('str') 
    edges_fit['ref'] = edges_fit['ref'].astype('str')  

    # %predict the rest of the map
    incl = edges_fit['cpk2'].isna()
    edges_fit.loc[incl,'cpk2'] = est.predict(edges_fit.loc[incl,osm_columns_cat + osm_columns_num + categorical_columns + numeric_columns])

    return edges_fit

# @st.experimental_memo
@st.cache
def transform_graph_new_edges(graph_proj,edges_fit,edges3):

    # in case under 0
    # todo: make sure never ends up under 0
    sumnum = sum(edges_fit['cpk2']<0)
    sumna = sum(edges_fit['cpk2'].isnull())
    print(f'under zero: {sumnum}')
    print(f'nans: {sumna}')
    edges_fit.loc[edges_fit['cpk2']<0,'cpk2'] = 0
    
 #add attribute of crash_per_km (from edges_fit)
    for key in graph_proj.edges:
        ind = edges3.index==key            
        graph_proj.edges[key]['cpk2'] = float(edges_fit[ind]['cpk2'])
            
    edges_fit2 = ox.graph_to_gdfs(graph_proj, nodes=False)
    
    return graph_proj, edges_fit2
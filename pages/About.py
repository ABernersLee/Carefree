#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov  8 15:40:06 2022

@author: alicebernerslee
"""
import streamlit as st
import os
import dill

import abt_plots
import data_process

_,_,header = st.columns([1,2,5])
_,header2 = st.columns([1,3])
# explain_map,edgemap = st.columns(2)
intro = st.container()

massdot,massdot_e = st.columns(2)
timeofday_e,timeofday = st.columns(2)
dayofweek,dayofweek_e = st.columns(2)
carsonly_e,carsonly = st.columns(2)
OSMdat,OSMdat_e = st.columns(2)
pipeline_e = st.container()
pipeline = st.container()
fitmap ,fitmap_e= st.columns(2)

explain_routes = st.container()
coming_soon = st.container()

# st.set_page_config(layout="centered",page_title='Carefree: About', page_icon=":bike:")

with header:
    st.title('Car**efree**')

with header2:
    st.header('Be carefree, leave your car at home.')
    
    
#### introduce project ####
with intro:
    st.markdown("\n\n",unsafe_allow_html=False)
    st.markdown("\n\n",unsafe_allow_html=False)
    body = ("##### Many people want to bike more often. Biking through cities is cheaper, reduces your emissions, is more pleasant, and allows you to enjoy city life more.\n\n"
            "##### However, fear of being hit by a car is a big deterrence.\n\n"
            "##### Carefree helps alleviate this fear by giving users safer routes through cities.\n\n"
            "###### Potential Carefree users include bike commuters and wanna-be bike commuters, parents who want to bike their kids to school and are especially worried about their kids being hit by cars, companies that use bike fleets for delivery, and those that currently use car fleets but are thinking of making the switch to bike fleets.")
    st.markdown(body, unsafe_allow_html=False)
    st.markdown("\n\n",unsafe_allow_html=False)
    st.markdown("\n\n",unsafe_allow_html=False)
        
        
    
#### show raw crash data ####

if os.path.isfile("data_dill/dat") :
    dat = dill.load(open("data_dill/dat","rb"))
else:
    dat = data_process.get_crash_data()
    dill.dump(dat, open("data_dill/dat", "wb"))
    
with massdot:
    st.dataframe(data=dat[:10])
    # , width=None, height=None, *, use_container_width=False)

with massdot_e:
    st.markdown("\n\n",unsafe_allow_html=False)
    st.markdown("\n\n",unsafe_allow_html=False)
    st.markdown("\n\n",unsafe_allow_html=False)
    st.markdown("\n\n",unsafe_allow_html=False)
    st.markdown("\n\n",unsafe_allow_html=False)
    body = "Some of the data for this project came from the Massachusetts Department of Transportation's crash data (MassDOT, [link](https://massdot-impact-crashes-vhb.opendata.arcgis.com/search?q=%22Person%20Level%20Details%22)).\n\nThis full data set contains 20 years of ~50,000 crashes. An example of that data is displayed on the left panel."
    st.markdown(body, unsafe_allow_html=False)




#### show some effects ####
with timeofday:

    has_cyc,only_car,has_cyc_tm,only_car_tm = abt_plots.get_cycl_dat(dat)
    
    fig = (abt_plots.plot_big_bar(
        has_cyc_tm,
        ['Early Morning','Morning','Noon','Evening','Night','Late Night'])
        )
    st.pyplot(fig)
    
with timeofday_e:
    st.markdown("\n\n",unsafe_allow_html=False)
    st.markdown("\n\n",unsafe_allow_html=False)
    st.markdown("\n\n",unsafe_allow_html=False)
    st.markdown("\n\n",unsafe_allow_html=False)
    st.markdown("\n\n",unsafe_allow_html=False)
    body = "Exploring this data revealed that bikers are not being hit by cars uniformly across time. To the right you can see that bikes are being hit by cars much more in the evening than at other times of day."
    st.markdown(body, unsafe_allow_html=False)
    

with dayofweek:    
    fig = (abt_plots.plot_big_bar(
        has_cyc,
        ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'])
        )
    st.pyplot(fig)
    
with dayofweek_e:
    st.markdown("\n\n",unsafe_allow_html=False)
    st.markdown("\n\n",unsafe_allow_html=False)
    st.markdown("\n\n",unsafe_allow_html=False)
    st.markdown("\n\n",unsafe_allow_html=False)
    st.markdown("\n\n",unsafe_allow_html=False)
    body = "In addition, more bike crashes occur on weekdays than weekends, as you can see by this plot on the left"
    st.markdown(body, unsafe_allow_html=False)

    
with carsonly:    
    fig = abt_plots.plot_cars_only(only_car_tm,only_car)         
    st.pyplot(fig)
   
with carsonly_e:
    st.markdown("\n\n",unsafe_allow_html=False)
    st.markdown("\n\n",unsafe_allow_html=False)
    st.markdown("\n\n",unsafe_allow_html=False)
    st.markdown("\n\n",unsafe_allow_html=False)
    st.markdown("\n\n",unsafe_allow_html=False)
    body = "These effects are not due to a general uptick of crashes during these times, as we can see when we look at car crashes that don't involve bikes. They show different trends across time."
    st.markdown(body, unsafe_allow_html=False)


#### show raw OSM data ####
if os.path.isfile("data_dill/edges") :
    edges = dill.load(open("data_dill/edges","rb"))
else:
    edges,_ = data_process.get_edges_nodes()
    dill.dump(edges, open("data_dill/edges", "wb"))
    
with OSMdat:
    fig = abt_plots.plot_OSM(edges)
    st.pyplot(fig)

with OSMdat_e:   
    st.markdown("\n\n",unsafe_allow_html=False)
    st.markdown("\n\n",unsafe_allow_html=False)
    st.markdown("\n\n",unsafe_allow_html=False)
    st.markdown("\n\n",unsafe_allow_html=False)
    st.markdown("\n\n",unsafe_allow_html=False)
    body = ("Another type of data used in this project is from Open Street Maps (OSM, [link](https://www.openstreetmap.org/)).\n\n"
            "Here, a graph of the city of **Somerville, MA** is plotted. Streets are depicted as white lines.\n\n"
            "This will be the backbone of the model we will build. We will bring the MassDOT crash data in, geocode it so that it is aligned with our OSM data and use it to predict danger for bikes on Somerville streets.")
    st.markdown(body, unsafe_allow_html=False)
    
    
#### show the pipeline ####
est = dill.load(open("data_dill/est","rb"))
    
with pipeline:
    st.text(est)

with pipeline_e:
    st.markdown("\n\n",unsafe_allow_html=False)
    st.markdown("\n\n",unsafe_allow_html=False)
    st.markdown("\n\n",unsafe_allow_html=False)
    st.markdown("\n\n",unsafe_allow_html=False)
    st.markdown("\n\n",unsafe_allow_html=False)
    body = "Using [sckit-learn](https://scikit-learn.org/stable/), a pipeline for a linear model is built out of features from both data sources. The schema of such a pipeline is shown bellow.\n\n(Note the engineered feature ""cpk2"" which was created from calculating the crashes per kilometer on each street, then for half of the data this value was propogated outward from streets with documented crashes. This feature allowed for an estimate of distnace from past crashes, based on only half of the streets' crashes per kilometer data.)"
    st.markdown(body, unsafe_allow_html=False)


    
#### show the model outcome ####
if os.path.isfile("data_dill/edges_fit2") :
    edges_fit2 = dill.load(open("data_dill/edges_fit2","rb"))
else:
    print("**error, need to build model")

with fitmap:
    fig = abt_plots.plot_edges_map(edges_fit2)
    st.pyplot(fig=fig)
    
with fitmap_e:
    st.markdown("\n\n",unsafe_allow_html=False)
    st.markdown("\n\n",unsafe_allow_html=False)
    st.markdown("\n\n",unsafe_allow_html=False)
    st.markdown("\n\n",unsafe_allow_html=False)
    st.markdown("\n\n",unsafe_allow_html=False)
    body = "After fitting the model, this is the map of Somerville with increasing danger plotted on the color axis. This model allows us to calculate safe routes from two addresses within this map."
    st.markdown(body, unsafe_allow_html=False)


with explain_routes:
    body = "To find routes through the map we first find the geolocation of the origin and destination address.\n\nWe then find the shortest and safest routes using [NetworkX](https://networkx.org/) to minimize either the length of the route or the estimated crashes/km along the route.\n\nWe then propose these two routes to the user, with estimates of time (based on an average bike speed of 217 meters/min or ~8mph) and calculate the danger per route by normalizing the danger by the length of the route."
    st.markdown(body, unsafe_allow_html=False)

with coming_soon:
    st.markdown("\n\n",unsafe_allow_html=False)
    st.markdown("\n\n",unsafe_allow_html=False)
    body = ("#### Some of the aspects that are coming soon:\n\n"
            "1. Normalizing the data by the measured activity of bikers in Somerville using data from the city of Someville ([link](https://data.somervillema.gov/dataset/Bicycle-Pedestrian-Counts/qu9x-4xq5/data))\n\n"
            "2. Adding elevation data to get better time estimates and allow users to choose between hilly and flat routes\n\n"
            "3. Including more street features in the model such as the presence and/or type of bike lane\n\n"
            "4. Because of the time-of-day effects seen above, adding time-of-day to the danger prediction would be nice. We would allow users to see if postponing a trip a bit would be safer.\n\n"
            "5. Hyper-parameter tuning and adding depictions of this and the cross-validation process to the About page")
    st.markdown(body, unsafe_allow_html=False)
    


    
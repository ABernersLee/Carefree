#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov  8 17:30:21 2022

@author: alicebernerslee
"""
import streamlit as st
import matplotlib.cm as cm
# import matplotlib as mpl
import matplotlib.pyplot as plt
COLOR = 'white'
plt.rcParams['text.color'] = COLOR
plt.rcParams['axes.labelcolor'] = COLOR
plt.rcParams['xtick.color'] = COLOR
plt.rcParams['ytick.color'] = COLOR
plt.rcParams['axes.edgecolor'] = COLOR
plt.rcParams['patch.facecolor'] = COLOR
plt.rcParams['axes.facecolor'] = 'black'
plt.rcParams['figure.facecolor'] = 'black'
plt.rcParams['font.size'] = 14

import numpy as np
import pandas as pd

def plot_edges_map(edges):
    cmap2 = plt.cm.get_cmap('plasma')
    sm = cm.ScalarMappable(norm=None, cmap=cmap2)
    dat = edges['cpk2']
    dat.loc[dat<=0] = np.nan
    dat = np.log10(edges['cpk2'])*100
    dat = (dat-min(dat))/(max(dat)-min(dat))
    print(min(dat),max(dat))
    ax = edges.plot(figsize=(16, 10), color=cmap2(dat), linewidth=3, alpha=1, legend=True)
    plt.colorbar(mappable=sm,ax=ax)
    plt.axis('off')
    fig = plt.gcf()
    fig.set_facecolor('k')
    return fig

@st.experimental_memo
def get_cycl_dat(dat):
    # making some new columns
    dat['datetime'] = pd.to_datetime(dat["CRASH_DATE_TEXT"] + ' ' + dat["CRASH_TIME"])
    dat['day_of_week'] = dat["datetime"].dt.day_name()
    b = [0,4,8,12,16,20,24]
    l = ['Late Night', 'Early Morning','Morning','Noon','Evening','Night']
    dat['time_of_day'] = pd.cut(dat['datetime'].dt.hour, bins=b, labels=l, include_lowest=True)
    
    # bike vs. car collisions
    isbike = dat["NON_MTRST_TYPE_CL"].str.contains('Cyclist',na=False,case=False)
    iscar = dat["NON_MTRST_TYPE_CL"].isna()
    has_cyc_tm = dat[isbike]["time_of_day"]
    only_car_tm = dat[iscar]["time_of_day"]
    has_cyc = dat[isbike]["day_of_week"]
    only_car = dat[iscar]["day_of_week"]
    return has_cyc,only_car,has_cyc_tm,only_car_tm

def plot_big_bar(df,labels):
# plot bikers
# ['Early Morning','Morning','Noon','Evening','Night','Late Night']
    plt.figure(figsize=[10,5])
    ax2 = plt.subplot(111)
    df.value_counts(normalize=True)[labels].plot(kind='bar',color='purple')
    ax2.set(ylim=(0, .4))
    plt.title('Car hits biker')
    plt.ylabel('Normalized count')
    # fig = plt.gcf()
    # fig.patch.set_facecolor('Black')
    return plt.gcf()

def plot_cars_only(only_car_tm,only_car):
    

    plt.figure(figsize=[12,5])
    
    # time of day for cars
    ax1 = plt.subplot(121)
    only_car_tm.value_counts(normalize=True)\
    [['Early Morning','Morning','Noon','Evening','Night','Late Night']].plot(kind='bar',color='gray')
    ax1.set(ylim=(0, .4))
    plt.title('Car crash no bikes: Time of day')
    plt.ylabel('Normalized count')
    
    # day of the week for cars
    ax2 = plt.subplot(122)
    only_car.value_counts(normalize=True)\
        [['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']].plot(kind='bar',color='gray')
    ax2.set(ylim=(0, .2))
    plt.title('Car crash no bikes: Day of the week')
    plt.ylabel('Normalized count')
    
    return plt.gcf()


def plot_OSM(edges):
    edges.plot(figsize=(16, 10), color='white', linewidth=0.5, alpha=.7)
    plt.axis('off')
    fig = plt.gcf()
    fig.set_facecolor('k')
    return fig
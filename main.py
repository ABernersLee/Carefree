#git version

import dill
import os

import data_process
import map_and_model
import user_map
import streamlit as st
from streamlit_folium import st_folium #, folium_static

#### Model features
osm_columns_cat = ['name','osmid','highway','oneway','ref'] 
osm_columns_num = ['width','lanes','maxspeed','cpk2']
categorical_columns = ['TERRAIN','SURFACE_TP','OPERATION','F_F_CLASS','TRAFY_DESCR_DESCR',
                       'SHLDR_LT_T','CURB','SHLDR_RT_T']
numeric_columns = ['PEAK_LANE','SURFACE_WD','LT_SIDEWLK','RT_SIDEWLK',
                   'SHLDR_LT_W','SHLDR_RT_W','SPEED_LIMIT'] #,'maxspeed']

#### example origin and destinations
placeholder_orig = '18 Oxford St, Somerville, MA'
placeholder_dest = '92 Pearson Rd, Somerville, MA'


st.set_page_config(layout="wide",page_title='Carefree', page_icon=":bike:")
_,_,header = st.columns([1,2,5])
_,header2 = st.columns([1,3])
map_search,map_disp = st.columns(2)
radio_text,_ = st.columns(2)


with header:
    st.title('Car**efree**')

with header2:
    st.header('Be carefree, leave your car at home.')
    
    
if os.path.isfile("data_dill/graph_fit") and os.path.isfile("data_dill/edges_fit2"):    
    # load processed data
    graph_fit = dill.load(open("data_dill/graph_fit","rb"))
    edges_fit2 = dill.load(open("data_dill/edges_fit2","rb"))
else:
    ## load raw data and process
    
    ### use data_process scripts to load and process data
    #get and merge street and crash data
    print('getting data')
    edges,nodes = data_process.get_edges_nodes()
    print('done get edges nodes')
    sm_crashes2g = data_process.get_crash_data()
    print('done get crash data')
    crash_streets = data_process.merge_crash_streets(sm_crashes2g, edges)
    print('done getting data')
    
    # get crash estimate
    st_num = data_process.create_crash_per_km(crash_streets)
    
    #merge crash estimate with edges of street graph
    merged_edges = data_process.get_merged_edges(st_num,edges,categorical_columns,osm_columns_cat,numeric_columns,osm_columns_num[:-1])
    print('done getting merged edges')
    graph_proj = data_process.make_graph_proj(edges, nodes, merged_edges,.5)
    print('done getting crash estimate')
    
    
    ### create the map and the model with that data
    
    #spread out the crash estimate into a new feature
    graph_proj, edges3 = map_and_model.spread_out_crash(graph_proj,.9)
    print('done spreading crash estimate')
    new_st_num = map_and_model.merge_new_var_in(edges3, st_num)
    print('done merging new estimate')
    
    #fit a model with the new variable and old ones
    est = map_and_model.make_fit_model(new_st_num,categorical_columns,osm_columns_cat,numeric_columns,osm_columns_num)
    print('done fitting model')
    
    # predict the rest of cpk2 to make the full map
    edges_fit = map_and_model.predict_map(new_st_num,edges3,est,categorical_columns,osm_columns_cat,numeric_columns,osm_columns_num)
    print('done predicting model')
    
    graph_fit,edges_fit2 = map_and_model.transform_graph_new_edges(graph_proj,edges_fit,edges3)
    print('done with all processing')
    
    
    dill.dump(graph_fit, open("data_dill/graph_fit", "wb"))
    dill.dump(edges_fit2, open("data_dill/edges_fit2", "wb"))
    dill.dump(est, open("data_dill/est", "wb"))
    dill.dump(edges3, open("data_dill/edges3", "wb"))




### make and update map

with map_search:
    
    st.subheader('Find the safest and fastest routes')
    
    
    input_orig = st.text_input(
        "Enter origin 👇",
        placeholder=placeholder_orig,
        )
    
    input_dest = st.text_input(
        "Enter destination 👇",
        placeholder=placeholder_dest,
        )
        
    
    st.session_state['checked'] = st.checkbox('Find routes',
              on_change=user_map.change_map,
               args = [input_orig, input_dest, graph_fit, edges_fit2]
              )

    st.radio("Which route would you like?",
        key="route_option",
        options=["Fastest", "Safest"])
    
    if 'dangr' in st.session_state and st.session_state['dangr']!='nan':
        dd = st.session_state['dangr']
        ll = st.session_state['lngth']
        st.write(f'Fastest: {round(ll[0],1)} min route with {round(dd[0],1)} crashes/year')
        st.write(f'Safest: {round(ll[1],1)} min route with {round(dd[1],1)} crashes/year')
        
    print('done with map search')
        
with map_disp:
    
    if 'mdict' not in st.session_state:
        mdict = dict()
        st.session_state['mdict'] = mdict
    
    if ('o' not in st.session_state): #or (not st.session_state['checked']):
        st.session_state['o'] = placeholder_orig
        st.session_state['d'] = 'nan'
        st.session_state['g'] = 'nan'
        st.session_state['e'] = 'nan'
        # m = user_map.default_plot(placeholder_orig,graph_fit)
        # m = user_map.default_plot(placeholder_orig,graph_fit)
        m = user_map.get_m(st.session_state['mdict'])
        st.session_state['m'] = m
    else:
        m = user_map.get_m(st.session_state['mdict'])
        
    # st.session_state['m'] = user_map.user_plot(st.session_state['o'],
    #                        st.session_state['d'],
    #                        st.session_state['g'],
    #                        st.session_state['e'],
    #                        st.session_state['m'],
    #                        st.session_state['route_option'])
    # m = get_m(st.session_state['d'],mdict,st.session_state)
    
    # st_map = st_folium(st.session_state['m'], width=700, height=500)
    st_map = st_folium(m, width=700, height=500)
    # folium_static(st_map)
    print('done with map disp')
    
 

    
    
### issues:
    #X plot on a better map instead of an image DONE
        #X got one route working, need to get the others DONE
        #X needs to change between DONE
        #X need to add a panel with the danger and estimated time DONE
        #X add to the chooseing part DONE
        #X make it zoom into the route DONE
    # change font color
    # fix the time (min) value
    # make the lines thicker
    # fix the double load problem
    # make the start and end icons be on the nearest nodes
    # figure out how to have two routes on the map at once
    # add an in between fast and safe routes
    # make another page with the aspects of the model
        # make page with just the map of danger 
        # havent done hyperparemeter tuning yet
            # do the edges to nodes for faster algorithm
        # havent brought in other features of streets
    # both of those issues are because of overlapping streets:
        # get better estimate of length
        # convert length to estimated time
        # using the median right now instead of the mean for danger
    # add cambridge and medford
#!/usr/bin/env python
# coding: utf-8

# # Building impacted by war fires
# # ==============================
# 
# This notebook focuses on analyzing the impact of war fires on buildings in Ukraine. It begins by importing necessary libraries and setting a development flag. The script then retrieves war fire data from a GitHub repository and reads both war fire and building datasets. Utilizing reverse geocoding, it determines the state of each building based on its geographical coordinates. The processed war fire data is saved, and subsequent steps involve filtering the data for specific Ukrainian states, creating a geometry column, and converting coordinates to the UTM coordinate system. Additionally, the code calculates the centroid of buildings and performs a spatial analysis to count the number of buildings within a 50-meter buffer of each war fire. The final results, detailing the impact of war fires on buildings, are saved to a CSV file. The script concludes by exporting the code as a Python script for future use.

# In[42]:


# Auto update notebook imports
#%load_ext autoreload
#%autoreload 2

# Backtrack to folder source directory if it doesn't already exist in path
import os
import sys

if os.path.basename(os.getcwd()) == "notebooks":
    os.chdir("..")

sys.path.append(os.getcwd())
print(os.getcwd())

import geopandas as gpd
import pandas as pd
from shapely.wkt import loads
import numpy as np
from shapely import wkt
from shapely.geometry import Point
from tqdm.notebook import tqdm
from urllib.request import urlretrieve

from geopy.geocoders import Nominatim
geolocator = Nominatim(user_agent="myexer")

from src.data import make_dataset

DEVELOPMENT = True

raw_filepath = "data/raw/"
interim_filepath = "data/interim/"
external_filepath = "data/external/"
processed_filepath = "data/processed/"


# In[43]:


raw_filepath = "data/raw/"
make_dataset.update_data(raw_filepath)


# In[44]:


# Read in the data
war_fire_csv_path = "./data/raw/war_fires_by_ADM3.csv"
war_fire_df = pd.read_csv(war_fire_csv_path)

building_data_csv_path = "./data/raw/building_shapes_file.csv"
output_df = pd.read_csv(building_data_csv_path)


# # Ukraine war fire dataset

# In[45]:


war_fire_df.head()


# In[46]:


war_fire_df.info()


# # Building Dataset

# In[47]:


output_df.head()


# In[48]:


output_df.info()


# # Reverse locate

# In[49]:


# If DEVELOPMENT is True, only run on first 100 rows
if DEVELOPMENT:
    war_fire_df = war_fire_df[:1000]

# Write the same code but add tqdm to see the progress of the loop
for idx, row in tqdm(war_fire_df.iterrows(), total=war_fire_df.shape[0]):
    war_fire_df.loc[war_fire_df.index[idx], 'state'] = make_dataset.find_states(row)


# In[ ]:


war_fire_df["state"].value_counts()


# In[ ]:


# Saving the war fire model back to a file
war_fire_df.to_csv("./data/processed/ukraine_war_fires_with_state_lookup.csv", index=False)


# In[ ]:


# Read processed war fire data
war_fire_df = pd.read_csv("./data/processed/ukraine_war_fires_with_state_lookup.csv")
war_fire_df["state"].value_counts()


# In[ ]:


# Limit war fires to states of interest
war_fire_df_state = war_fire_df[war_fire_df["state"].isin(["Odesa Oblast","Chernihiv Oblast", "Sumy Oblast", "Kharkiv Oblast","Luhansk Oblast","Donetsk Oblast","Zaporizhia Oblast","Kherson Oblast","Mykolaiv Oblast"])]
war_fire_df_state.head() 


# In[ ]:


war_fire_df_state["state"].value_counts()


# In[ ]:


# Add in the geometry column
war_fire_df_state['geometry'] = war_fire_df_state.apply(lambda row: Point(row['LATITUDE'], row['LONGITUDE']), axis=1)
war_fire_df_state["geometry"].head()


# # calculate UTM

# In[ ]:


# change to GeoDataFrame
# geo_build_df = gpd.GeoDataFrame(buildings_df)
# geo_build_df = geo_build_df.set_geometry("geometry_wkt_cent")


# In[ ]:


# from pyproj import Proj
# pp = Proj(proj='utm',zone=10,ellps='WGS84', preserve_units=False)

# geo_build_df["xx"], geo_build_df["yy"]= pp(geo_build_df["geometry_wkt_cent"].x.values,geo_build_df["geometry_wkt_cent"].y.values)
# # My_data["X"] = xx
# # My_data["Y"] = yy 


# In[ ]:


# First, convert WKT column to geometries
#buildings_df_state['geometry_wkt_cent2'] = gpd.GeoSeries.from_wkt(buildings_df_state['geometry_wkt_cent'])

# Then create a GeoDataFrame, setting the geometry to the converted geometries
# geo_build_df = gpd.GeoDataFrame(buildings_df_state, geometry='geometry_wkt_cent')


# In[ ]:


# geo_build_df.crs = 'epsg:32635'
# # change the projection of geodf
# geo_build_df_2 = geo_build_df.to_crs(epsg=32635)
# print(geo_build_df_2)


# In[ ]:


#geo_build_df_2["geometry_wkt_cent"]


# # Buffer 

# In[ ]:


# import geopandas as gpd
# from shapely.geometry import Point
# from pprint import pprint

# buffer_radius_m = 500
# buffered_gdf = geo_build_df_2.copy()

# buffered_gdf['geometry_wkt_cent_buff'] = buffered_gdf.buffer(buffer_radius_m)  # 1 degree of latitude is approximately 111.32 km
# # Print the buffered GeoDataFrame

# pprint(buffered_gdf)


# In[ ]:


#pip install pyproj --upgrade


# In[ ]:


import pyproj
print(pyproj.__version__)


# ### with utm conversion
# 

# In[ ]:


# In summary, the code first ensures that the GeoDataFrame has a defined CRS, 
# estimates the UTM CRS, and then reprojects the data to that UTM CRS. 
# The code then applies a buffer of 50 meters around each geometry in the 
# UTM-projected GeoDataFrame. Finally the code sets the geometry of the GeoDataFrame to the buffered geometries.
geo_warfires_df = gpd.GeoDataFrame(war_fire_df_state, geometry='geometry')
geo_warfires_df.set_crs(epsg=4326, inplace=True)
utm_crs = geo_warfires_df.estimate_utm_crs()
geo_warfires_df_utm = geo_warfires_df.to_crs("EPSG:32635")

# Then, apply the buffer in meters
buffer_radius_m = 50  # Buffer radius in meters
geo_warfires_df_utm['geometry_buff'] = geo_warfires_df_utm.buffer(buffer_radius_m)
geo_warfires_df_utm = geo_warfires_df_utm.set_geometry("geometry_buff")
geo_warfires_df_utm['geometry_buff'].head()


# # Buildings dataset

# ## Convert string geometry to integer

# In[ ]:


output_df['geometry_wkt'] = output_df['geometry'].apply(lambda x: loads(x) if x is not None else None)


# In[ ]:


buildings_df = output_df.copy()
buildings_df.head()


# In[ ]:


print(buildings_df["buildingle"].isna().sum()/len(buildings_df))


# In[ ]:


buildings_df["geometry_wkt_cent"] = np.nan


# In[ ]:


# buildings_df["geometry_wkt_cent"] = buildings_df["geometry_wkt"].apply(lambda x: x.centroid )
buildings_df['geometry_wkt_cent'] = buildings_df['geometry_wkt'].apply(lambda geom: Point(geom.centroid.y, geom.centroid.x))

# This will result in a column 'centroid' with tuples where the first element is latitude and the second is longitude.


# In[ ]:


buildings_df["geometry_wkt_cent"]


# ## Find the intersection of war_fires and buildings
# 

# ### Buildings dataset with utm conversion
# 

# In[ ]:


# The main purpose of this code is to convert the geometries in the building GeoDataFrame 
# from the original geographic coordinate system (WGS 84) to a UTM projected coordinate 
#  system (EPSG 32635). This might be useful for spatial analysis or visualization in a 
# local coordinate system, which can be more suitable for certain tasks.
geo_buildings_df = gpd.GeoDataFrame(buildings_df, geometry='geometry_wkt_cent')
geo_buildings_df.set_crs(epsg=4326, inplace=True)
geo_buildings_df_utm = geo_buildings_df.to_crs("EPSG:32635")


# ### How many buildings are within 50 meters of warfires

# In[ ]:


# Function to count buildings within a given buffer polygon
def count_buildings_in_buffer(buffer, buildings_gdf):
    # Use the within method to check if buildings are within the buffer zone
    return buildings_gdf.within(buffer).sum()

# Rewrite the code above using tqdm to see the progress of the loop
for idx, row in tqdm(geo_warfires_df_utm.iterrows(), total=geo_warfires_df_utm.shape[0]):
    geo_warfires_df_utm.loc[idx, 'building_count'] = count_buildings_in_buffer(row['geometry_buff'], geo_buildings_df_utm)


# In[ ]:


geo_warfires_df_utm['geometry_buff']


# In[ ]:


# Take a look at buildings that have been affected by war fires
geo_warfires_df_utm[geo_warfires_df_utm['building_count']  > 0].head()


# In[ ]:


# Count the total number of buildings in each state
geo_warfires_df_utm.groupby('state')['building_count'].sum()


# In[ ]:


geo_warfires_df_utm.to_csv("./data/processed/buildings_impacted_by_war_fires.csv", index=False)


# In[ ]:


# Convert to a python script and save in local folder
get_ipython().system("jupyter nbconvert --to script ./notebooks/*.ipynb --output-dir='./notebooks/python_scripts/python_scripts'")


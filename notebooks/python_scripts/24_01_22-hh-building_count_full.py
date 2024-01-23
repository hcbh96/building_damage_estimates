#!/usr/bin/env python
# coding: utf-8

# # Visualising Building Damage
# # ==========================
# The provided Python script is designed for data analysis and visualization within a Jupyter Notebook environment. It begins by setting up the necessary environment, importing libraries, and adjusting the working directory if needed. The script loads a dataset from a CSV file, containing information about buildings impacted by war fires, into a Pandas DataFrame. It then conducts an analysis, displaying unique values of the 'building_count' column. Subsequently, the script creates two Folium maps to visualize the spatial distribution of affected buildings. The first map marks locations where buildings have been impacted by war fires, displaying building counts as pop-up information. The second map highlights areas with war fires and a non-null 'geometry_buff,' using circular markers to indicate the number of affected buildings. Finally, the script converts the Jupyter Notebook to a Python script using the `nbconvert` command. Note that the effectiveness of the script depends on the specifics of the dataset and the intended analysis.

# In[1]:


# Auto update notebook imports
#%load_ext autoreload
# %autoreload 2

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
import folium
from geopandas import GeoDataFrame


# In[2]:


impacted_buildings_filename = "./data/processed/buildings_impacted_by_war_fires.csv"
geo_warfires = pd.read_csv(impacted_buildings_filename)
geo_warfires.head()


# ### Numbers of building that are affected by war fire (using Intersection of war_fires and buildings)

# In[3]:


geo_warfires['building_count'].unique()


# ### Showing building_count based on geometry

# In[4]:


# Filter out rows where building_count is not equal to 0
filtered_data = geo_warfires[geo_warfires['building_count'] != 0]

n = folium.Map(location=[filtered_data['LATITUDE'].mean(), filtered_data['LONGITUDE'].mean()], zoom_start=10)

for index, row in filtered_data.iterrows():
    folium.Marker(
        [row['LATITUDE'], row['LONGITUDE']],
        popup=f"Building Count: {row['building_count']}"
    ).add_to(n)

n.save("./notebooks/figures/ukr_warfire_build_count_markers2.html")


# ### War fires with buff and number of buildings are affected

# In[5]:


import pandas as pd
import folium


# Filter out rows where building_count is greater than 0 and based on geometry_buff
filtered_data = geo_warfires[(geo_warfires['building_count'] > 0) & (geo_warfires['geometry_buff'].notnull())]

m = folium.Map(location=[filtered_data['LATITUDE'].mean(), filtered_data['LONGITUDE'].mean()], zoom_start=10)

for index, row in filtered_data.iterrows():
    folium.Circle(
        radius=10,  # Adjust the radius of the circle as needed
        location=[row['LATITUDE'], row['LONGITUDE']],
        popup=f"Building Count: {row['building_count']}",
        color='crimson',  # Color of the circle outline
        fill=True,
        fill_color='crimson'  # Fill color of the circle
    ).add_to(m)

m.save("./notebooks/figures/ukr_warfire_build_count_markers_with_geobuff.html")

m.save("./notebooks/figures/ukr_warfire_build_count.html")


# In[ ]:


# Convert to a python script and save in local folder
get_ipython().system("jupyter nbconvert --to script ./notebooks/*.ipynb --output-dir='./notebooks//python_scripts'")


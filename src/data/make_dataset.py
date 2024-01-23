# -*- coding: utf-8 -*-
import click
import logging
from pathlib import Path
from dotenv import find_dotenv, load_dotenv

import geopandas as gpd
import pandas as pd
from shapely.wkt import loads
import numpy as np
from shapely import wkt
from shapely.geometry import Point
from tqdm.notebook import tqdm
from urllib.request import urlretrieve

from tqdm.notebook import tqdm

from geopy.geocoders import Nominatim
geolocator = Nominatim(user_agent="myexer")

DEVELOPMENT = True

# Click commands in future might be a nice interface
#@click.command()
#@click.argument('input_filepath', type=click.Path(exists=True))
#@click.argument('output_filepath', type=click.Path())
def main(raw_filepath, interim_filepath, processed_filepath, DEVELOPMENT=False):
    """ Runs data processing scripts to turn raw data from (../raw) into
        cleaned data ready to be analyzed (saved in ../processed).
    """
    logger = logging.getLogger(__name__)
    logger.info('making final data set from raw data')

    # Read in the war fire data
    war_fires = pd.read_csv(raw_filepath + "war_fires_by_ADM3.csv")

    # Read in the building datas
    buildings = gpd.read_file(raw_filepath + "building_shapes_file.csv")

    # If DEVELOPMENT is True, only run on first 100 rows
    if DEVELOPMENT:
        war_fires = war_fires[:1000]

    logger.info('processing war fire data')
    # Find the war fire locations by state
    for idx, row in tqdm(war_fires.iterrows(), total=war_fires.shape[0]):
        war_fires.loc[war_fires.index[idx], 'state'] = find_states(row)

    # Saving the war csv to an interim file
    war_fires.to_csv(interim_filepath + "war_fires_by_ADM3.csv")

    # Read in the interim war fire data
    war_fires = pd.read_csv(interim_filepath + "war_fires_by_ADM3.csv")

    # Add in a geometry column to the war fire data
    war_fires['geometry'] = war_fires.apply(lambda row: Point(row['LATITUDE'], row['LONGITUDE']), axis=1)

    # In summary, the code first ensures that the GeoDataFrame has a defined CRS, 
    # estimates the UTM CRS, and then reprojects the data to that UTM CRS. 
    # The code then applies a buffer of 50 meters around each geometry in the 
    # UTM-projected GeoDataFrame. Finally the code sets the geometry of the GeoDataFrame to the buffered geometries.
    geo_war_fires = gpd.GeoDataFrame(war_fires, geometry='geometry')
    geo_war_fires.set_crs(epsg=4326, inplace=True)
    geo_war_fires = geo_war_fires.to_crs("EPSG:32635")

    # Then, apply the buffer in meters
    buffer_radius_m = 50  # Buffer radius in meters
    geo_war_fires['geometry_buff'] = geo_war_fires.buffer(buffer_radius_m)
    geo_war_fires = geo_war_fires.set_geometry("geometry_buff")
    geo_war_fires['geometry_buff'].head()

    logger.info('processing building data')
    # Create a column in the buildings dataset
    buildings['geometry_wkt'] = buildings['geometry'].apply(lambda x: loads(x) if x is not None else None)
    buildings["geometry_wkt_cent"] = np.nan
    buildings['geometry_wkt_cent'] = buildings['geometry_wkt'].apply(lambda geom: Point(geom.centroid.y, geom.centroid.x))

    # The main purpose of this code is to convert the geometries in the building GeoDataFrame 
    # from the original geographic coordinate system (WGS 84) to a UTM projected coordinate 
    #  system (EPSG 32635). This might be useful for spatial analysis or visualization in a 
    # local coordinate system, which can be more suitable for certain tasks.
    geo_buildings = gpd.GeoDataFrame(buildings, geometry='geometry_wkt_cent')
    geo_buildings.set_crs(epsg=4326, inplace=True)
    geo_buildings = geo_buildings.to_crs("EPSG:32635")


    # Rewrite the code above using tqdm to see the progress of the loop
    for idx, row in tqdm(geo_war_fires.iterrows(), total=geo_war_fires.shape[0]):
        geo_war_fires.loc[idx, 'building_count'] = count_buildings_in_buffer(row['geometry_buff'], geo_buildings)

    # Save the data to a csv file
    geo_war_fires.to_csv(processed_filepath + "buildings_impacted_by_war_fires.csvs")

def count_buildings_in_buffer(buffer, buildings_gdf):
    # Use the within method to check if buildings are within the buffer zone
    return buildings_gdf.within(buffer).sum()
    
def find_states(row):
    """
    The find_states function takes a row of data containing 
    latitude and longitude information (retrieved from columns named 
    "LATITUDE" and "LONGITUDE") and performs reverse geocoding using the 
    geolocator object. It constructs a coordinate string, retrieves 
    location information in English, and extracts the state information 
    from the raw address data. The function then returns the state 
    information obtained from the reverse geocoding process. 
    """
       
    lat, lon = row["LATITUDE"], row["LONGITUDE"]
    
    cord = f"{lat}, {lon}"
    location = geolocator.reverse(cord, exactly_one=True,language="en")
    address = location.raw['address']
    state = address.get('state', '')
    # if desired it is possible to additionally extract the 
    # ['town', 'village', 'hamlet', 'municipality', 'locality', 'city']
    
    return state

def update_data(raw_filepath):
    """ Downloads the latest data from the source and saves it to the
        output_filepath.
    """
    logger = logging.getLogger(__name__)
    logger.info('downloading data from source')

    # Download the data from the ssource
    url = "https://github.com/TheEconomist/the-economist-war-fire-model/raw/master/output-data/war_fires_by_ADM3.csv"

    urlretrieve(url, raw_filepath + url.split("/")[-1])



if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # not used in this stub but often useful for finding various files
    project_dir = Path(__file__).resolve().parents[2]

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())

    main()

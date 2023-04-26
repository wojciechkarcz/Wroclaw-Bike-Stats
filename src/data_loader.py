from bs4 import BeautifulSoup
import requests
import pandas as pd
import numpy as np
from geopy.distance import geodesic
from google.oauth2 import service_account
from datetime import datetime
import sys


# url path to a website with chronologically ordered list of links to .csv files with bike rides data
url = 'https://opendata.cui.wroclaw.pl/dataset/wrmprzejazdy_data/resource_history/c737af89-bcf7-4f7d-8bbc-4a0946d7006e'


def get_file_data(url):
    """
    Function returns the precise url of the latest data file and its name
    """
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    download_url = soup.find('a', {'class':'heading'})['href']
    filename = soup.find('a', {'class':'heading'})['title']
    
    # If the date in the filename does not match the current date, abort the program and raise an error
    if filename.split('_')[2] == datetime.now().strftime('%Y-%#m-%#d'):    
        return download_url, filename
    else:
        sys.exit('outdated date error')


def distance(row): 
    """
    Utility function which calculates the geodesic distance between two bike stations in km
    """
    add1 = (row['lat_start'], row['lon_start']) 
    add2 = (row['lat_end'], row['lon_end']) 
    try: 
        return (geodesic(add1, add2).km) 
    except: 
        return np.nan


def transform_data(df, stations):
    """
    Function responsible for data cleaning and transformation (changing columns names, removing empty records, 
    adding bike station coordinates, caluculating distance, etc.)
    """
    df['Stacja wynajmu'] = df['Stacja wynajmu'].apply(lambda x: x.replace(u'\xa0',u''))
    df['Stacja wynajmu'] = df['Stacja wynajmu'].apply(lambda x: x.rstrip())

    df['Stacja zwrotu'] = df['Stacja zwrotu'].apply(lambda x: x.replace(u'\xa0',u''))
    df['Stacja zwrotu'] = df['Stacja zwrotu'].apply(lambda x: x.rstrip())

    labels = df.loc[(df['Stacja wynajmu'].str[0].isin(['#'])) | (df['Stacja zwrotu'].str[0].isin(['#']))].index
    df = df.drop(index=labels, axis=0)

    df = pd.merge(df, stations, left_on='Stacja wynajmu', right_on='station_name', how='left')
    df = pd.merge(df, stations, left_on='Stacja zwrotu', right_on='station_name', how='left', suffixes=('_start','_end'))

    df = df.drop(columns=['station_name_start','station_name_end'])
    df = df.rename(columns={'UID wynajmu':'uid','Numer roweru':'bike_number','Data wynajmu':'start_time','Data zwrotu':'end_time','Stacja wynajmu':'rental_place','Stacja zwrotu':'return_place','Czas trwania':'duration'})

    df['start_time'] = pd.to_datetime(df['start_time'])
    df['end_time'] = pd.to_datetime(df['end_time'])

    df['distance'] = np.nan
    df['distance'] = df.apply(lambda row: distance(row), axis=1)
    return df


def load_to_gbq(df):
    """
    Function takes as an argument a datframe and loads into the Bigquery database. In this case
    database authorization is handled using private google json key.
    """
    credentials = service_account.Credentials.from_service_account_file('/path/to/google_key.json')
    df.to_gbq('db_name.table_name', project_id='project_id', if_exists='append', progress_bar=False, credentials=credentials)


def main():
    download_url, filename = get_file_data(url)
    df = pd.read_csv(download_url)
    stations = pd.read_csv('data/bike_stations.csv')     
    new_df = transform_data(df, stations)
    
    # Saving transformed and cleaned data locally into .csv file
    new_df.to_csv(filename, index=False)
    
    load_to_gbq(new_df)
    

if __name__ == '__main__':
    main() 



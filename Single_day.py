import streamlit as st
from datetime import datetime, timedelta
from google.oauth2 import service_account
import pandas as pd
import numpy as np
import plotly.express as px


# Credentials to database connection, db private key hidden using Streamlit st.secrets variable
credentials = service_account.Credentials.from_service_account_info(
    {
        "type": "service_account",
        "project_id": st.secrets['project_id'],
        "private_key_id": st.secrets['private_key_id'],
        "private_key": st.secrets['private_key'],
        "client_email": st.secrets['client_email'],
        "client_id": st.secrets['client_id'],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": st.secrets['client_x509_cert_url']
    },
)

@st.cache_data
def load_data(start_date, end_date):
    """
    Loads data between start and end date from Bigquery database and returns in form of dataframe. Function uses @st.cache_data decorator to store data in the cache.
    """
    query = 'SELECT * FROM citybike_wroclaw_2023.bike_rides_2023 WHERE start_time > \'{}\' AND start_time < \'{}\''.format(start_date, end_date)
    df = pd.read_gbq(query, project_id=st.secrets['project_id'], credentials=credentials)
    return df

@st.cache_data
def load_last_date():
    """
    Function retrieves the most recent date from the database
    """
    query = 'SELECT start_time FROM citybike_wroclaw_2023.bike_rides_2023 ORDER BY start_time DESC LIMIT 1'
    df = pd.read_gbq(query, project_id=st.secrets['project_id'], credentials=credentials)
    return np.datetime_as_string(df.tail(1)['start_time'].values[0],unit='D')

def date_range(date):
    """
    Returns start date (most recent date) and end day (the day before)
    """
    end_date = date.strftime('%Y-%m-%d') + ' 23:59:59' 
    start_date = (datetime.strptime(end_date,'%Y-%m-%d %H:%M:%S')-timedelta(days=1)).strftime('%Y-%m-%d')
    return start_date, end_date

def get_bike_rides_metrics(df, date):
    """
    Returns basic metrics regarding bike rides on provided date as an argument 
    """
    #df_day = df.loc[df['start_time'].dt.date == pd.Timestamp(date)]
    #df_day_before = df.loc[df['start_time'].dt.date == pd.Timestamp(date-timedelta(days=1))]

    date = date.strftime('%Y-%m-%d')

    df_day = df.loc[df['start_time'].dt.strftime('%Y-%m-%d') == date]
    df_day_before = df.loc[df['start_time'].dt.strftime('%Y-%m-%d') < date]

    total_rides = df_day['uid'].count()
    total_rides_delta = total_rides - df_day_before['uid'].count()

    avg_ride_duration = round(df_day.loc[df_day['duration'] > 1]['duration'].mean(),1)
    avg_ride_duration_delta = round(avg_ride_duration - round(df_day_before.loc[df_day_before['duration'] > 1]['duration'].mean(),1),1)

    avg_ride_length = round(df_day.loc[df_day['distance'] > 1]['distance'].mean(),2)
    avg_ride_length_delta = round(avg_ride_length - round(df_day_before.loc[df_day_before['distance'] > 1]['distance'].mean(),2),2)
    return total_rides, total_rides_delta, avg_ride_duration, avg_ride_duration_delta, avg_ride_length, avg_ride_length_delta

def dist_plot_bike_rides(df, date):
    """
    Outputs bar chart with bike rides rental hours distribution on given date
    """
    date = date.strftime('%Y-%m-%d')
    data = df.loc[df['start_time'].dt.strftime('%Y-%m-%d') == date].groupby(df['start_time'].dt.hour)['uid'].count()

    #data = df.loc[df['start_time'].dt.date == pd.Timestamp(date)].groupby(df['start_time'].dt.hour)['uid'].count()
    return st.bar_chart(data)

def create_df_bike_stations(df, date):
    """
    Creates datframe with all the details regarding bike station (number of rentals, returns, and difference between rentals/returns) on given date
    """
    
    date = date.strftime('%Y-%m-%d')
    rental_df = df.loc[df['start_time'].dt.strftime('%Y-%m-%d') == date].groupby('rental_place')['uid'].count().reset_index(name='rental_count')
    return_df = df.loc[df['start_time'].dt.strftime('%Y-%m-%d') == date].groupby('return_place')['uid'].count().reset_index(name='return_count')

    #rental_df = df.loc[df['start_time'].dt.date == pd.Timestamp(date)].groupby('rental_place')['uid'].count().reset_index(name='rental_count')
    #return_df = df.loc[df['start_time'].dt.date == pd.Timestamp(date)].groupby('return_place')['uid'].count().reset_index(name='return_count')

    temp = pd.merge(rental_df,return_df, left_on='rental_place', right_on='return_place', how='left')
    temp = temp.drop(columns='return_place')
    temp = temp.rename(columns={'rental_place':'bike_station'})
    temp['return_count'] = temp['return_count'].fillna(0)
    temp['diff'] = temp['return_count'] - temp['rental_count']
    temp = temp[temp['bike_station'] != 'Poza stacją']
    temp = temp.sort_values(ascending=False, by='rental_count')
    return temp

def revenue(row):
    """
    Utility function to calculate revenue on each bike ride
    """
    x = row['duration']
    if x > 20 and x < 61:
        return 2
    elif x >= 61:
        if x > 720:
            return 2 + ((x // 60) * 4) + 300
        else:
            return 2 + ((x // 60) * 4)
    else:
        return 0

def load_df_current_day(df, date): 
    """
    Loads data only from given date and returns a dataframe
    """
    date = date.strftime('%Y-%m-%d')
    return df.loc[df['start_time'].dt.strftime('%Y-%m-%d') == date]

def create_df_misc_info(info):
    """
    Creates a datframe with misc information about bike rides (eg. numbr of loop rides, number of bikes returned outside bike station, estimated revenue, etc.) and returns dictionary
    """
    info_stations_outside = info.loc[info['return_place'] == 'Poza stacją']['uid'].count()
    info_stations_outside_ratio = round(info_stations_outside / info['uid'].count() * 100,1)
    info_outside_bikes_fine = info_stations_outside * 5
    info_total_distance = round(info['distance'].sum(),2)
    info_loop = info.loc[(info['rental_place'] == info['return_place']) & (info['rental_place'] != 'Poza stacją') & (info['duration'] > 1)]['uid'].count()
    
    info['revenue'] = info.apply(lambda row: revenue(row), axis=1)
    info_total_revenue = info['revenue'].sum()

    info_df = {'Bikes returned out of bike stations':('{} ({} %)').format(info_stations_outside,info_stations_outside_ratio),
            'Total fine for returning bike out of bike station': ('{} PLN').format(info_outside_bikes_fine),
            'Total distance*': ('{} km').format(info_total_distance),
            'Total loops (same rental/return station)': info_loop,
            'Estimated total revenue**': ('{} PLN').format(info_total_revenue)
            }
    return info_df

def create_df_traffic_map(info):
    """
    Transforms dataframe (info) in order to create a new dataframe (g1) with number of rentals at each bike stations at every hour throughout the day 
    """
    test_geo2 = info.groupby(['rental_place',info['start_time'].dt.hour,'lat_start','lon_start'])['uid'].count().reset_index().rename(columns=({'uid':'count','start_time':'hour'}))
    g1 = test_geo2.groupby(['hour','rental_place']).agg(count = ('count','sum')).reset_index()
    g1[['lat_start','lon_start']] = test_geo2.groupby(['hour','rental_place'])[['lat_start','lon_start']].first().reset_index()[['lat_start','lon_start']]
    return g1

def plot_traffic_map(df):
    """
    Creates the plotly map/chart with animation of changing number of bike rental at each station
    """
    fig = px.scatter_mapbox(df, lat="lat_start", lon="lon_start", hover_name='rental_place', 
                            size='count', animation_frame='hour', size_max=25, zoom=11, width=0, height=750
                            )
    fig.update_layout(mapbox_style="carto-positron")
    return st.plotly_chart(fig)


def main():
    """
    Main function displays all Streamlit elements on a webpage
    """

    # Page configuration and title
    st.set_page_config(page_title="Wroclaw Bike Stats", page_icon="🚴‍♂️", layout='centered')
    st.sidebar.header("Wrocław Bike Stats")
    st.sidebar.markdown('It is a web application that aggregates current data on city bike rides in Wrocław, Poland')

    st.title(':bike: Single day data')
    st.markdown('On this page you can find city bike ride statistics for one specific day. Below you can choose the day from the calendar that interests you. ***Note:*** The data is released with a two-day delay.')
    st.markdown('#####')

    # Loading the most actual date from the database
    current_date = load_last_date()
    st.write(st.session_state.day)

    if 'day' not in st.session_state:
        st.session_state.day = datetime.strptime(current_date,'%Y-%m-%d')

    temp_date = st.session_state.day
    start_date, end_date = date_range(st.session_state.day)

    # Date input widget
    colA, colB = st.columns([1,2],gap='medium')

    with colA:
        st.date_input(":date: **Pick the date:**", key='day', value=temp_date, min_value=datetime.strptime('2023-03-02','%Y-%m-%d'), max_value=datetime.strptime(current_date,'%Y-%m-%d'))
        #st.date_input(":date: **Pick the date:**", key='day', value=temp_date, min_value=datetime.strptime('2023-03-02','%Y-%m-%d'), max_value=datetime.strptime(current_date,'%Y-%m-%d'))
        # adding something to change here
    
    title_date = st.session_state.day.strftime('%#d %B %Y')
    title_weekday = st.session_state.day.strftime('%A')

    st.markdown('---')

    # Data loading (current day and day before)
    df = load_data(start_date, end_date)

    st.markdown('### '+ title_date + ' | ' + title_weekday)
    st.markdown('###')

    total_rides, total_rides_delta, avg_ride_duration, avg_ride_duration_delta, avg_ride_length, avg_ride_length_delta = get_bike_rides_metrics(df, st.session_state.day)


    # Ride time distribution chart and essential stats/metrics
    col1, col2 = st.columns([4,1],gap='medium')

    with col1:
        st.markdown('Number of bike rentals by hour')
        dist_plot_bike_rides(df, st.session_state.day)

    with col2:
        st.metric(label="Total rides", value=total_rides, delta=str(total_rides_delta))
        st.metric(label="Avg. ride time", value='{} m'.format(avg_ride_duration), delta=str(avg_ride_duration_delta))
        st.metric(label="Avg. ride distance", value='{} km'.format(avg_ride_length), delta=str(avg_ride_length_delta))


    # Table with top rental stations
    temp = create_df_bike_stations(df, st.session_state.day)

    st.markdown('#### 📊 Bike stations')
    st.markdown('The table shows bike stations ranked in terms of the number of rentals throughout the day. You can click on any column title to sort the data relative to it.')
    st.dataframe(temp, height=210, use_container_width=True)


    # Table with misc info 
    st.markdown('#####')
    st.markdown('#### 🎈 Misc data')
    st.markdown('A table containing additional information related to bike rentals for that day.')

    info = load_df_current_day(df, st.session_state.day)
    info_df = create_df_misc_info(info)
    
    st.table(info_df)


    # Map with bike rental frequency throughout the day
    st.markdown('#####')
    st.markdown('#### 🗺️ Activity map')
    st.markdown('Map showing the number of rentals at each bike station per hour. Click on the play button and see the traffic animation on all stations throughout the day. '+
                'If you hover your mouse over the bubble, you will see the name of the station and the exact number of rentals during a specific hour of the day.')

    g1 = create_df_traffic_map(info)
    plot_traffic_map(g1)

 
    # Footnotes
    st.markdown('#')
    st.markdown('#')
    st.info('''\* - *the total distance traveled by users during the day is calculated as the sum of the distances between stations in a straight line. Of course, we don\'t know what specific route users take, but this data gives general overview about the total length of rides that day.*  
    \** - *the total revenue obtained on a given day for renting bikes is in accordance with the current Wrocław City Bike price list. However, it does not include the revenue from e-bikes because the available data does not include information about the type of bicycles.*  ''')


if __name__ == '__main__':
    main()
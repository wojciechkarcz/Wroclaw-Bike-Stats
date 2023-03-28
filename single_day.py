import streamlit as st
import datetime
from datetime import datetime, timedelta
from google.oauth2 import service_account
#import pandas_gbq
import pandas as pd
import numpy as np
import plotly.express as px


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


st.set_page_config(
    page_title="Wroclaw Bike Stats",
    page_icon="🚴‍♂️",
    layout='centered'
    )

st.sidebar.header("Wrocław Bike Stats")
st.sidebar.markdown('It is a web application that aggregates data on the Wrocław City Bike')

st.title('🗓️ Single day data')

@st.cache_data
def load_data(start_date, end_date):
    #credentials = service_account.Credentials.from_service_account_file('google_key.json')
    query = 'SELECT * FROM citybike_wroclaw_2023.bike_rides_2023 WHERE start_time > \'{}\' AND start_time < \'{}\''.format(start_date, end_date)
    df = pd.read_gbq(query, project_id=st.secrets['project_id'], credentials=credentials)
    return df

def load_last_date():
    #credentials = service_account.Credentials.from_service_account_file('google_key.json')
    query = 'SELECT start_time FROM citybike_wroclaw_2023.bike_rides_2023 ORDER BY start_time DESC LIMIT 1'
    df = pd.read_gbq(query, project_id=st.secrets['project_id'], credentials=credentials)
    return np.datetime_as_string(df.tail(1)['start_time'].values[0],unit='D')


current_date = load_last_date()

if 'day' not in st.session_state:
    st.session_state.day = datetime.strptime(current_date,'%Y-%m-%d')

temp_date = st.session_state.day

end_date = st.session_state.day.strftime('%Y-%m-%d') + ' 23:59:59' 
start_date = (datetime.strptime(end_date,'%Y-%m-%d %H:%M:%S')-timedelta(days=1)).strftime('%Y-%m-%d')

df = load_data(start_date, end_date)

title_date = st.session_state.day.strftime('%#d %B %Y')
title_weekday = st.session_state.day.strftime('%A')

html_str = f"""
<h3>{title_date}</h3><h4>{title_weekday}</h4><br><br>
"""
st.markdown(html_str, unsafe_allow_html=True)

# Date input widget
st.date_input("Pick the date", key='day', value=temp_date, min_value=datetime.strptime('2023-03-02','%Y-%m-%d'), max_value=datetime.strptime(current_date,'%Y-%m-%d'))

# Creating data frame with all data for current date
data = df.loc[df['start_time'].dt.date == pd.Timestamp(st.session_state.day)].groupby(df['start_time'].dt.hour)['uid'].count()


# Defining variables to first chart and data

df_day = df.loc[df['start_time'].dt.date == pd.Timestamp(st.session_state.day)]
df_day_before = df.loc[df['start_time'].dt.date == pd.Timestamp(st.session_state.day-timedelta(days=1))]

total_rides = df_day['uid'].count()
total_rides_delta = total_rides - df_day_before['uid'].count()

avg_ride_duration = round(df_day.loc[df_day['duration'] > 1]['duration'].mean(),1)
avg_ride_duration_delta = round(avg_ride_duration - round(df_day_before.loc[df_day_before['duration'] > 1]['duration'].mean(),1),1)

avg_ride_length = round(df_day.loc[df_day['distance'] > 1]['distance'].mean(),2)
avg_ride_length_delta = round(avg_ride_length - round(df_day_before.loc[df_day_before['distance'] > 1]['distance'].mean(),2),2)


# Ride time distribution chart and basic stats

col1, col2 = st.columns([4,1],gap='medium')

with col1:
    st.markdown('**Number of bike rents by hour**')
    st.bar_chart(data)

with col2:
    #st.write('Basic stats')
    st.metric(label="Total rides", value=total_rides, delta=str(total_rides_delta))
    st.metric(label="Avg. ride time", value='{} m'.format(avg_ride_duration), delta=str(avg_ride_duration_delta))
    st.metric(label="Avg. ride distance", value='{} km'.format(avg_ride_length), delta=str(avg_ride_length_delta))


# Table with top rental places

rental_df = df.loc[df['start_time'].dt.date == pd.Timestamp(st.session_state.day)].groupby('rental_place')['uid'].count().reset_index(name='rental_count')
return_df = df.loc[df['start_time'].dt.date == pd.Timestamp(st.session_state.day)].groupby('return_place')['uid'].count().reset_index(name='return_count')

temp = pd.merge(rental_df,return_df, left_on='rental_place', right_on='return_place', how='left')

temp = temp.drop(columns='return_place')
temp = temp.rename(columns={'rental_place':'bike_station'})
temp['return_count'] = temp['return_count'].fillna(0)
temp['diff'] = temp['return_count'] - temp['rental_count']
temp = temp[temp['bike_station'] != 'Poza stacją']

st.markdown('**Top rental bike stations**')
st.markdown('You can sort each parameter in the table below')
st.dataframe(temp.sort_values(ascending=False, by='rental_count'), height = 210, use_container_width=True)


# Table with misc info 

info = df.loc[df['start_time'].dt.date == pd.Timestamp(st.session_state.day)]

info_stations_outside = info.loc[info['return_place'] == 'Poza stacją']['uid'].count()
info_stations_outside_ratio = round(info_stations_outside / info['uid'].count() * 100,1)
info_outside_bikes_fine = info_stations_outside * 5
info_total_distance = round(info['distance'].sum(),2)
info_loop = info.loc[(info['rental_place'] == info['return_place']) & (info['rental_place'] != 'Poza stacją') & (info['duration'] > 1)]['uid'].count()

def revenue(row):
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

info['revenue'] = info.apply(lambda row: revenue(row), axis=1)
info_total_revenue = info['revenue'].sum()

info_df = {'Bikes returned out of bike stations':('{} ({} %)').format(info_stations_outside,info_stations_outside_ratio),
           'Total fine for returning bike outside bike station': ('{} PLN').format(info_outside_bikes_fine),
           'Total distance*': ('{} km').format(info_total_distance),
           'Total loops (same rental/return station)': info_loop,
           'Estimated total revenue**': ('{} PLN').format(info_total_revenue)
           }

st.markdown('**Additional info**')
st.table(info_df)


# Map with bike rental frequency over the hours in that day

test_geo2 = info.groupby(['rental_place',info['start_time'].dt.hour,'lat_start','lon_start'])['uid'].count().reset_index().rename(columns=({'uid':'count','start_time':'hour'}))
g1 = test_geo2.groupby(['hour','rental_place']).agg(count = ('count','sum')).reset_index()
g1[['lat_start','lon_start']] = test_geo2.groupby(['hour','rental_place'])['lat_start','lon_start'].first().reset_index()[['lat_start','lon_start']]

fig2 = px.scatter_mapbox(g1, lat="lat_start", lon="lon_start", hover_name='rental_place', 
                        size='count', animation_frame='hour', size_max=25, zoom=11, width=0, height=750
                        )

fig2.update_layout(mapbox_style="carto-positron")

st.markdown('**Map of bike renting activity**')

st.write(fig2)
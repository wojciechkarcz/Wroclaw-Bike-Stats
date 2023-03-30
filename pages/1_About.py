import streamlit as st


st.set_page_config(page_title="Wrocław Bike Stats",
                   page_icon="🚴‍♂️",
                    layout='centered')

# Sidebar section 
st.sidebar.header("Wrocław Bike Stats")
st.sidebar.markdown('It is a web application that aggregates current data on city bike rides in Wrocław, Poland')

# Main body section
st.title('About')

st.markdown('''***Wrocław Bike Stats*** is a web application that aggregates and processes open data on the rides of the City Bike in Wrocław, Poland. The data is publicly available on the official website of [the municipal office in Wrocław](https://opendata.cui.wroclaw.pl/organization/6e9968c2-c271-45dd-b90d-150520ae74b1?tags=rower+miejski)
''')


st.image('img/nextbike_rower_wroclaw.jpg', caption='credit: Togamek, CC BY-SA 3.0, via Wikimedia Commons', width=600)

st.markdown('''The application focuses on the analysis of current data from 2023. However, open resources also contain historical data, which will be analyzed in a later order.

If you want to learn more about the operation of the Wrocław City Bike, you can find all the information on the official website:  
[wroclawskirower.pl](https://wroclawskirower.pl/)
''')

st.markdown('##')

st.markdown('#### App roadmap')
st.markdown('''The current version of the application is only the first stage of development and works on a "proof of concept" basis. Below is a general plan for introducing further features.
 
⏲️ **Time interval** - a page will be added with the option of selecting a time interval and displaying various interesting data for this period. It will be possible, for example, to compare how the number of rentals changes within a month, or which bike stations are the most popular.  
            
📍 **Bike stations** - this page will be devoted to the analysis of data directly related to bike stations. There you will find information such as the list of the most popular stations, the busiest hours for each station, or the most popular directions of departures and arrivals to the station. 
            
📔 **2022 data** - a page dedicated to the analysis of data on all bike rides from 2022.  
            
🌦️ **Weather data** – adding basic weather data to the single day data view''')

st.markdown('##')

st.markdown('#### Documentation')
st.markdown(''' The Wrocław Bike Stats project is completely open-source. All code and technical documentation is on Github: [link to Github repo](https://github.com/wojciechkarcz)
''')

st.markdown('##')

st.markdown('#### Follow us on Twitter')
st.markdown('''[@WroclwBikeStats](https://twitter.com/WroclwBikeStats)  
This profile contains all the latest information about updates and new features of the application. You will also find there various interesting finds and insights that can be discovered while working on the development of the application.
''')


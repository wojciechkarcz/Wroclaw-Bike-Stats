import streamlit as st


st.set_page_config(page_title="Wrocław Bike Stats",
                   page_icon="🚴‍♂️",
                    layout='centered')

st.title('About')

st.sidebar.header("Wrocław Bike Stats")
st.sidebar.markdown('It is a web application that aggregates current data on city bike rides in Wrocław, Poland')

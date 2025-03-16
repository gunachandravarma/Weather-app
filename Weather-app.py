import streamlit as st
import numpy as np
import pandas as pd
import requests
import datetime as dt
import matplotlib.pyplot as plt
import seaborn as sns
import folium
from streamlit_folium import folium_static
from sklearn.linear_model import LinearRegression
import plotly.express as px
import plotly.graph_objects as go

# CSS for UI styling
st.markdown("""
    <style>
        .main { background-color: #f4f4f4; }
        h1 { color: #ff6600; }
        .stButton>button { background-color: #ff6600; color: white; border-radius: 10px; }
        .stMetric { font-size: 1.2em; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.sidebar.title(":mostly_sunny: Weather Dashboard")
st.sidebar.markdown("Enter a city name to fetch real-time weather data.")
city = st.sidebar.text_input("🌍 Enter City Name")
comparison_city = st.sidebar.text_input("🌍 Compare with City (Optional)")

# Fetching the data
BASE_URL = "http://api.openweathermap.org/data/2.5/weather?"
FORECAST_URL = "https://api.openweathermap.org/data/3.0/onecall?"
API_KEY = "1b6c06ebaf0bbbf68cacf2b9238b80e8"

def get_coordinates(city):
    url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={API_KEY}"
    response = requests.get(url).json()
    if response and isinstance(response, list) and len(response) > 0:
        return response[0].get('lat'), response[0].get('lon')
    return None, None

if st.sidebar.button("Fetch Weather 🌤️"):
    try:
        lat, lon = get_coordinates(city)
        comp_lat, comp_lon = get_coordinates(comparison_city) if comparison_city else (None, None)
        if lat and lon:
            url = f"{BASE_URL}appid={API_KEY}&q={city}"
            response = requests.get(url).json()
            forecast_url = f"{FORECAST_URL}lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
            forecast_response = requests.get(forecast_url).json()

            if response.get('main'):
                temp_celsius = response['main']['temp'] - 273.15
                feels_like_celsius = response['main']['feels_like'] - 273.15
                wind_speed = response['wind']['speed']
                humidity = response['main']['humidity']
                description = response['weather'][0]['description'].capitalize()

                st.title(f"🌤️ {city} Weather Report")

                st.subheader("📜 Weather Description")
                st.write(f"The current weather in {city} is characterized by {description}. "
                         f"The temperature is around {temp_celsius:.2f}°C, with a humidity level of {humidity}%. "
                         f"The wind is blowing at {wind_speed} meters per second, making it feel like {feels_like_celsius:.2f}°C. "
                         "It is advisable to dress accordingly and be prepared for the weather conditions.")


                col1, col2 = st.columns(2)
                with col1:
                    st.metric("🌡️ Temperature", f"{temp_celsius:.2f}°C")
                    st.metric("💧 Humidity", f"{humidity}%")
                with col2:
                    st.metric("🌡️ Feels Like", f"{feels_like_celsius:.2f}°C")
                    st.metric("💨 Wind Speed", f"{wind_speed} m/s")

                with st.expander("🗺️ Weather Map"):
                    weather_map = folium.Map(location=[lat, lon], zoom_start=8)
                    folium.Marker([lat, lon], tooltip=f"{city} Weather", popup=f"{description}, {temp_celsius:.2f}°C").add_to(weather_map)

                    # Adding Weather Overlays
                    folium.TileLayer("https://tile.openweathermap.org/map/temp_new/{z}/{x}/{y}.png?appid=" + API_KEY,
                                     attr="OpenWeatherMap", name="Temperature Overlay").add_to(weather_map)
                    folium.TileLayer("https://tile.openweathermap.org/map/clouds_new/{z}/{x}/{y}.png?appid=" + API_KEY,
                                     attr="OpenWeatherMap", name="Cloud Cover").add_to(weather_map)
                    folium.TileLayer("https://tile.openweathermap.org/map/precipitation_new/{z}/{x}/{y}.png?appid=" + API_KEY,
                                     attr="OpenWeatherMap", name="Precipitation Overlay").add_to(weather_map)
                    folium.TileLayer("https://tile.openweathermap.org/map/wind_new/{z}/{x}/{y}.png?appid=" + API_KEY,
                                     attr="OpenWeatherMap", name="Wind Speed Overlay").add_to(weather_map)
                    folium.LayerControl().add_to(weather_map)
                    folium_static(weather_map)

                tab1, tab2, tab3 = st.tabs(["📈 Climate Forecast", "📊 Data Analysis", "🌍 Comparison Mode"])

                with tab1:
                    if 'daily' in forecast_response:
                        dates = [dt.datetime.utcfromtimestamp(day['dt']).strftime('%Y-%m-%d') for day in forecast_response['daily']]
                        temps = [day['temp']['day'] for day in forecast_response['daily']]
                        df_forecast = pd.DataFrame({'Date': dates, 'Temperature (°C)': temps})
                        fig = px.line(df_forecast, x='Date', y='Temperature (°C)', title='Temperature Forecast')
                        st.plotly_chart(fig)

                      # Predict next temperature trend using Linear Regression
                    X = np.array(range(len(temps))).reshape(-1, 1)
                    y = np.array(temps).reshape(-1, 1)
                    model = LinearRegression()
                    model.fit(X, y)
                    future_days = np.array(range(len(temps), len(temps) + 3)).reshape(-1, 1)
                    predicted_temps = model.predict(future_days)

                    st.subheader("🔮 Predicted Temperature for Next 3 Days")
                    for i, temp in enumerate(predicted_temps.flatten()):
                        st.write(f"Day {i+1}: {temp:.2f}°C")

                with tab2:
                    st.subheader("📊 Heatmap of Temperature Trends")
                    if 'daily' in forecast_response:
                        temp_matrix = np.array([day['temp']['day'] for day in forecast_response['daily']]).reshape(-1, 1)
                        fig = px.imshow(temp_matrix, color_continuous_scale='Viridis', title='Heatmap of Temperature Variations')
                        st.plotly_chart(fig)

                    st.subheader("📊 Box Plot for Weather Metrics")
                    weather_df = pd.DataFrame({
                        "Metric": ["Temperature", "Feels Like", "Humidity", "Wind Speed"],
                        "Value": [temp_celsius, feels_like_celsius, humidity, wind_speed]
                    })
                    fig = px.box(weather_df, y='Value', x='Metric', title='Box Plot for Weather Metrics')
                    st.plotly_chart(fig)

                    st.subheader("📊 Histogram for Temperature Distribution")
                    fig = px.histogram(df_forecast, x='Temperature (°C)', nbins=10, title='Temperature Distribution')
                    st.plotly_chart(fig)

                with tab3:
                    if comp_lat and comp_lon:
                        comp_url = f"{BASE_URL}appid={API_KEY}&q={comparison_city}"
                        comp_response = requests.get(comp_url).json()
                        comp_temp = comp_response['main']['temp'] - 273.15
                        comp_humidity = comp_response['main']['humidity']

                        comp_df = pd.DataFrame({
                            "City": [city, comparison_city],
                            "Temperature (°C)": [temp_celsius, comp_temp],
                            "Humidity (%)": [humidity, comp_humidity]
                        })
                        fig = px.bar(comp_df, x='City', y=['Temperature (°C)', 'Humidity (%)'], barmode='group', title='City Weather Comparison')
                        st.plotly_chart(fig)
                    else:
                        st.warning("❌ Please enter the comparison city!")
            else:
                st.error("❌ City not found! Please enter a valid city name.")
        else:
            st.error("❌ Unable to get location coordinates!")
    except requests.exceptions.RequestException as e:
        st.error(f"⚠️ Network error: {e}")

import streamlit as st
import numpy as np
import pandas as pd
import requests
import datetime as dt
import matplotlib.pyplot as plt
import seaborn as sns
import folium
from folium.plugins import MarkerCluster
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
city = st.sidebar.text_input("🌍 Enter City Name","Hyderabad")
comparison_city = st.sidebar.text_input("🌍 Compare with City (Optional)","Jaipur")

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
                        humidity_levels = [day['humidity'] for day in forecast_response['daily']]
                        wind_speeds = [day['wind_speed'] for day in forecast_response['daily']]

                        df_forecast = pd.DataFrame({'Date': dates, 'Temperature (°C)': temps, 'Humidity (%)': humidity_levels, 'Wind Speed (m/s)': wind_speeds})

                        # Temperature Forecast Line Chart
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

                        # AQICN Integration
                        AQI_TOKEN = "2f5934ac7d76e648fbb65214601a63643faa1435"  # Replace with your actual AQI token
                        aqi_url = f"https://api.waqi.info/feed/{city}/?token={AQI_TOKEN}"
                        aqi_response = requests.get(aqi_url).json()

                        if aqi_response.get("status") == "ok":
                            aqi_data = aqi_response["data"]
                            aqi = aqi_data.get("aqi", "N/A")
                            dominant_pollutant = aqi_data.get("dominentpol", "N/A").upper()
                            iaqi = aqi_data.get("iaqi", {})

                            st.subheader("🌫️ Air Quality Index (AQI)")
                            st.metric("🌍 AQI Level", f"{aqi}")
                            st.write(f"**Dominant Pollutant:** {dominant_pollutant}")
                            def aqi_category(aqi):
                                if aqi <= 50:
                                    return "Good 😊"
                                elif aqi <= 100:
                                    return "Moderate 🙂"
                                elif aqi <= 150:
                                    return "Unhealthy for Sensitive Groups 😷"
                                elif aqi <= 200:
                                    return "Unhealthy 😷"
                                elif aqi <= 300:
                                    return "Very Unhealthy 🥵"
                                else:
                                    return "Hazardous ☠️"

                            st.write(f"**Air Quality Status:** {aqi_category(aqi)}")
                            
                             # Create AQI Map using Folium with the Tile Layer from AQICN
                            m = folium.Map(location=[lat, lon], zoom_start=12, control_scale=True)

                            # Add the AQI tile layer from AQICN Tile Map Service
                            aqi_tile_url = "https://tiles.aqicn.org/tiles/usepa-aqi/{z}/{x}/{y}.png"
                            folium.TileLayer(
                                tiles=aqi_tile_url,
                                attr="AQICN",
                                name="Air Quality Index",
                                overlay=True,
                                control=True
                            ).add_to(m)

                            # Add a marker with AQI information
                            folium.Marker(
                                location=[lat, lon],
                                popup=f"City: {city}\nAQI: {aqi}\nDominant Pollutant: {dominant_pollutant}",
                                icon=folium.Icon(color='blue', icon='info-sign')
                            ).add_to(m)

                            # Show the map
                            st.subheader("🗺️ AQI Map")
                            st.components.v1.html(m._repr_html_(), height=500)


                            # Display pollutants if available
                            pollutant_values = {k.upper(): v['v'] for k, v in iaqi.items() if 'v' in v}
                            if pollutant_values:
                                df_aqi = pd.DataFrame(pollutant_values.items(), columns=["Pollutant", "Value"])
                                fig = px.bar(df_aqi, x='Pollutant', y='Value', title='Air Pollutant Levels')
                                st.plotly_chart(fig)
                            else:
                                st.info("No detailed pollutant data available.")

                            
                       
                        # Humidity Forecast Line Chart
                        fig = px.line(df_forecast, x='Date', y='Humidity (%)', title='Humidity Forecast')
                        st.plotly_chart(fig)

                        # Wind Speed Forecast Line Chart
                        fig = px.line(df_forecast, x='Date', y='Wind Speed (m/s)', title='Wind Speed Forecast')
                        st.plotly_chart(fig)

                        # Combined Forecast Chart
                        fig = px.line(df_forecast, x='Date', y=['Temperature (°C)', 'Humidity (%)', 'Wind Speed (m/s)'],
                                      title='Combined Weather Forecast')
                        st.plotly_chart(fig)

                        # Box Plot for Forecasted Weather Parameters
                        forecast_melted = df_forecast.melt(id_vars='Date', var_name='Metric', value_name='Value')
                        fig = px.box(forecast_melted, x='Metric', y='Value', title='Box Plot of Forecasted Weather Parameters')
                        st.plotly_chart(fig)

                        # Scatter Plot for Temperature vs Humidity
                        fig = px.scatter(df_forecast, x='Temperature (°C)', y='Humidity (%)',
                                         title='Temperature vs Humidity', trendline='ols')
                        st.plotly_chart(fig)

                with tab2:
                    st.subheader("📊 Weather Data Analysis")

                    #st.subheader("📊 Heatmap of Temperature Trends")
                    if 'daily' in forecast_response:
                        temp_matrix = np.array([day['temp']['day'] for day in forecast_response['daily']]).reshape(-1, 1)
                        fig = px.imshow(temp_matrix, color_continuous_scale='Viridis', title='Heatmap of Temperature Variations')
                        st.plotly_chart(fig)

                    # Histogram for Temperature Distribution
                    fig = px.histogram(df_forecast, x='Temperature (°C)', nbins=10, title='Temperature Distribution')
                    st.plotly_chart(fig)

                    # Box Plot for Temperature, Humidity, Wind Speed, and Pressure
                    fig = px.box(df_forecast.melt(id_vars='Date', var_name='Metric', value_name='Value'), x='Metric', y='Value', title='Box Plot of Weather Metrics')
                    st.plotly_chart(fig)

                    # Correlation Heatmap for Weather Metrics
                    corr_matrix = df_forecast.drop(columns=['Date']).corr()
                    fig = px.imshow(corr_matrix, text_auto=True, color_continuous_scale='RdBu_r', title='Correlation Heatmap')
                    st.plotly_chart(fig)

                    # Line Chart for Temperature Trends
                    fig = px.line(df_forecast, x='Date', y='Temperature (°C)', title='Temperature Trends Over Time')
                    st.plotly_chart(fig)

                    # Scatter Plot for Temperature vs Wind Speed
                    fig = px.scatter(df_forecast, x='Temperature (°C)', y='Wind Speed (m/s)', title='Temperature vs Wind Speed', trendline='ols')
                    st.plotly_chart(fig)


                with tab3:
                    if comp_lat and comp_lon:
                        comp_url = f"{BASE_URL}appid={API_KEY}&q={comparison_city}"
                        comp_response = requests.get(comp_url).json()
                        comp_temp = comp_response['main']['temp'] - 273.15
                        comp_humidity = comp_response['main']['humidity']
                        comp_wind_speed = comp_response['wind']['speed']

                        # Data for comparison
                        comp_df = pd.DataFrame({
                            "City": [city, comparison_city],
                            "Temperature (°C)": [temp_celsius, comp_temp],
                            "Humidity (%)": [humidity, comp_humidity],
                            "Wind Speed (m/s)": [wind_speed, comp_wind_speed]
                        })

                        # Bar Chart Comparison
                        fig = px.bar(comp_df, x='City', y=['Temperature (°C)', 'Humidity (%)', 'Wind Speed (m/s)'],
                                     barmode='group', title='City Weather Comparison')
                        st.plotly_chart(fig)

                        # Temperature Trend Line Chart
                        if 'daily' in forecast_response and 'daily' in comp_response:
                            comp_temps = [day['temp']['day'] for day in forecast_response['daily']]
                            comp_dates = [dt.datetime.utcfromtimestamp(day['dt']).strftime('%Y-%m-%d') for day in forecast_response['daily']]
                            df_comparison = pd.DataFrame({
                                'Date': comp_dates,
                                f'{city} Temperature (°C)': temps,
                                f'{comparison_city} Temperature (°C)': comp_temps
                            })
                            fig = px.line(df_comparison, x='Date', y=[f'{city} Temperature (°C)', f'{comparison_city} Temperature (°C)'],
                                          title='Temperature Trend Comparison')
                            st.plotly_chart(fig)

                        # Box Plot Comparison
                        fig = px.box(comp_df.melt(id_vars='City', var_name='Metric', value_name='Value'),
                                     x='Metric', y='Value', color='City',
                                     title='Box Plot Comparison of Weather Metrics')
                        st.plotly_chart(fig)

                        # Radar Chart for Weather Metrics
                        categories = ['Temperature (°C)', 'Humidity (%)', 'Wind Speed (m/s)']
                        radar_fig = go.Figure()

                        # Define custom colors for each city
                        colors = ['rgba(0,128,255,0.5)', 'rgba(255,99,132,0.5)']  # Fill colors with opacity
                        line_colors = ['blue', 'red']  # Border line colors

                        for i, city_name in enumerate([city, comparison_city]):
                            radar_fig.add_trace(go.Scatterpolar(
                                r=comp_df.iloc[i, 1:].values,
                                theta=categories,
                                fill='toself',
                                name=city_name,
                                fillcolor=colors[i],
                                line=dict(color=line_colors[i], width=2)
                            ))

                        radar_fig.update_layout(
                            polar=dict(
                                radialaxis=dict(visible=True)
                            ),
                            showlegend=True,
                            title='Weather Comparison Radar Chart'
                        )

                        st.plotly_chart(radar_fig)
                    else:
                        st.warning("❌ Please enter the comparison city!")
        else:
            st.error("❌ Unable to get location coordinates!")
    except requests.exceptions.RequestException as e:
        st.error(f"⚠️ Network error: {e}")
        else:
            st.error("❌ Unable to get location coordinates!")
    except requests.exceptions.RequestException as e:
        st.error(f"⚠️ Network error: {e}")

# external_apis/weather_api.py

import requests
import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry
import pytz

# All the functions like get_lat_lon_from_zip,
# fetch_weather_data, hourly_weather_data, and history_data will be here.

def get_lat_lon_from_zip(zipcode: str, country: str = "us") -> tuple[float, float, str, str]:
    """
    Get latitude, longitude, city, and state from ZIP code.
    Returns: (latitude, longitude, city_name, state_name)
    """
    url = f"http://api.zippopotam.us/{country}/{zipcode}"
    try:
        response = requests.get(url)
        response.raise_for_status()  # This will raise an HTTPError for bad responses (4xx or 5xx)
        data = response.json()

        lat = float(data['places'][0]['latitude'])
        lng = float(data['places'][0]['longitude'])
        city = data['places'][0]['place name']
        state = data['places'][0]['state']
        
        # --- THE FIX IS HERE ---
        # We are now returning all four values as expected.
        return lat, lng, city, state

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err} for zip {zipcode}")
        raise  # Re-raise the exception to be caught by the calling tool function
    except (KeyError, IndexError) as e:
        print(f"Error parsing JSON response for zip {zipcode}: {e}")
        raise # Re-raise the exception

def fetch_weather_data(latitude: float, longitude: float,forecast_days: int) -> pd.DataFrame:
    """
    Fetch weather data from Open-Meteo API using provided latitude and longitude.
    """
    # Setup Open-Meteo API client
    cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
    	"latitude": latitude,
    	"longitude": longitude,
    	"daily": ["temperature_2m_max", "temperature_2m_min", "wind_speed_10m_max", "wind_gusts_10m_max"],
    	"models": "best_match",
    	"current": ["wind_speed_10m", "is_day", "precipitation", "rain"],
    	"timezone": "auto",
    	"forecast_days": forecast_days,
    	"wind_speed_unit": "mph",
    	"temperature_unit": "fahrenheit"
    }
    responses = openmeteo.weather_api(url, params=params)
    
    # Process first location. Add a for-loop for multiple locations or weather models
    response = responses[0]
    print(f"Coordinates {response.Latitude()}°N {response.Longitude()}°E")
    print(f"Elevation {response.Elevation()} m asl")
    print(f"Timezone {response.Timezone()}{response.TimezoneAbbreviation()}")
    print(f"Timezone difference to GMT+0 {response.UtcOffsetSeconds()} s")
    
    # Current values. The order of variables needs to be the same as requested.
    current = response.Current()
    current_wind_speed_10m = current.Variables(0).Value()
    current_is_day = current.Variables(1).Value()
    current_precipitation = current.Variables(2).Value()
    current_rain = current.Variables(3).Value()

    print(f"Current time {current.Time()}")
    print(f"Current wind_speed_10m {current_wind_speed_10m}")
    print(f"Current is_day {current_is_day}")
    print(f"Current precipitation {current_precipitation}")
    print(f"Current rain {current_rain}")
    
    # Process daily data. The order of variables needs to be the same as requested.
    daily = response.Daily()
    daily_temperature_2m_max = daily.Variables(0).ValuesAsNumpy()
    daily_temperature_2m_min = daily.Variables(1).ValuesAsNumpy()
    daily_wind_speed_10m_max = daily.Variables(2).ValuesAsNumpy()
    daily_wind_gusts_10m_max = daily.Variables(3).ValuesAsNumpy()
    
    # daily_data = {"date": pd.date_range(
    # 	start = pd.to_datetime(daily.Time(), unit = "s", utc = True),
    # 	end = pd.to_datetime(daily.TimeEnd(), unit = "s", utc = True),
    # 	freq = pd.Timedelta(seconds = daily.Interval()),
    # 	inclusive = "left"
    # )}

    # Decode the timezone from response (it's a byte string)
    timezone_str = response.Timezone().decode("utf-8")
    timezone = pytz.timezone(timezone_str)
    
    # Create full daily datetime range in UTC
    daily_utc = pd.date_range(
        start=pd.to_datetime(daily.Time(), unit="s", utc=True),
        end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=daily.Interval()),
        inclusive="left"
    )
    
    # Convert to local timezone and extract only the date part
    daily_local_dates = daily_utc.tz_convert(timezone).date
    
    # Assign to daily_data
    daily_data = {
        "date": daily_local_dates
    }
    
    daily_data["temperature_2m_max"] = daily_temperature_2m_max
    daily_data["temperature_2m_min"] = daily_temperature_2m_min
    daily_data["wind_speed_10m_max"] = daily_wind_speed_10m_max
    daily_data["wind_gusts_10m_max"] = daily_wind_gusts_10m_max

    return pd.DataFrame(data=daily_data)



def hourly_weather_data(latitude: float, longitude: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Fetches hourly and daily weather data from Open-Meteo API based on provided latitude and longitude.
    Returns: (hourly_dataframe, daily_dataframe)
    """
    # Setup Open-Meteo client
    cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    # Weather API parameters 
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": ["temperature_2m_max", "temperature_2m_min", "wind_speed_10m_max", "wind_gusts_10m_max"],
        "hourly": ["temperature_2m", "relative_humidity_2m", "rain", "wind_speed_10m", "soil_moisture_1_to_3cm", "soil_temperature_6cm", "sunshine_duration"],
        "models": "best_match",
        "current": ["wind_speed_10m", "is_day", "precipitation", "rain"],
        "timezone": "auto",
        "forecast_days": 1,
        "wind_speed_unit": "mph",
        "temperature_unit": "fahrenheit"
    }

    # Call API
    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]

    # Process hourly data
    hourly = response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    hourly_relative_humidity_2m = hourly.Variables(1).ValuesAsNumpy()
    hourly_rain = hourly.Variables(2).ValuesAsNumpy()
    hourly_wind_speed_10m = hourly.Variables(3).ValuesAsNumpy()
    hourly_soil_moisture_1_to_3cm = hourly.Variables(4).ValuesAsNumpy()
    hourly_soil_temperature_6cm = hourly.Variables(5).ValuesAsNumpy()
    hourly_sunshine_duration = hourly.Variables(6).ValuesAsNumpy()
    
    # hourly_data = {"date": pd.date_range(
    # 	start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
    # 	end = pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
    # 	freq = pd.Timedelta(seconds = hourly.Interval()),
    # 	inclusive = "left"
    # )}

    
    # Get timezone string from API and convert from byte string
    timezone_str = response.Timezone().decode("utf-8")
    timezone = pytz.timezone(timezone_str)
    
    # Create full hourly datetime range in UTC
    hourly_datetimes = pd.date_range(
        start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
        end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=hourly.Interval()),
        inclusive="left"
    )
    
    # Convert to local timezone
    hourly_local = hourly_datetimes.tz_convert(timezone)
    
    # Format to include both date and time in 12-hour format (e.g., Jun 05, 01:00 PM)
    formatted_datetime = hourly_local.strftime('%b %d, %I:%M %p')  # Example: "Jun 05, 01:00 PM"
    
    # Assign to hourly_data dictionary
    hourly_data = {
        "datetime": formatted_datetime
    }
    
    hourly_data["temperature_2m"] = hourly_temperature_2m
    hourly_data["relative_humidity_2m"] = hourly_relative_humidity_2m
    hourly_data["rain"] = hourly_rain
    hourly_data["wind_speed_10m"] = hourly_wind_speed_10m
    hourly_data["soil_moisture_1_to_3cm"] = hourly_soil_moisture_1_to_3cm
    hourly_data["soil_temperature_6cm"] = hourly_soil_temperature_6cm
#    hourly_data["sunshine_duration"] = hourly_sunshine_duration

    hourly_dataframe = pd.DataFrame(data = hourly_data)

    # Process daily data
    daily = response.Daily()
    daily_data = {
        "date": pd.date_range(
            start=pd.to_datetime(daily.Time(), unit="s", utc=True),
            end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=daily.Interval()),
            inclusive="left"
        ),
        "temperature_2m_max": daily.Variables(0).ValuesAsNumpy(),
        "temperature_2m_min": daily.Variables(1).ValuesAsNumpy(),
        "wind_speed_10m_max": daily.Variables(2).ValuesAsNumpy(),
        "wind_gusts_10m_max": daily.Variables(3).ValuesAsNumpy()
    }

    daily_dataframe = pd.DataFrame(daily_data)


    return hourly_dataframe, daily_dataframe

def history_data(latitude: float, longitude: float, past_days: int) -> pd.DataFrame:

    # Setup Open-Meteo client
    cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)
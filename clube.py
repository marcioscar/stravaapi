
import pandas as pd
import streamlit as st

st.set_page_config(layout="wide")
df_strava = pd.read_csv('atividades_unicas.csv')
df_strava['athlete.fullname'] = df_strava['firstname'] + ' ' + df_strava['lastname']
df_strava['moving_time_minutes'] = round(df_strava['moving_time']/60, 2)



cols = ['athlete.fullname','name', 'type', 'distance',   
         'data_atual', 'distance_km', 'pace_real','moving_time_minutes'
       ]
df_strava['moving_time_minutes'] = round(df_strava['moving_time']/60, 2)

df_strava['distance_km'] = round(df_strava['distance'] / 1000, 2)

df_strava['pace'] = df_strava['moving_time_minutes'] / df_strava['distance_km']

df_strava['avg_speed_kmh'] = round(60/df_strava['pace'], 2)


def kmh_to_min_km(speed_kmh):
    if speed_kmh > 0:  # Evitar divisão por zero
        pace = 60 / speed_kmh
        minutes = int(pace)
        seconds = int((pace - minutes) * 60)
        return f"{minutes}:{seconds:02d} min/km"
    else:
        return None  # Retorna None para velocidades inválidas

df_strava['avg_speed_kmh'] = pd.to_numeric(df_strava['avg_speed_kmh'], errors='coerce')
df_strava['pace_real'] = df_strava['avg_speed_kmh'].apply(kmh_to_min_km)

corridas = df_strava[cols]
runs = corridas.loc[corridas['type'] == 'Run' ].sort_values(by='athlete.fullname')
runs







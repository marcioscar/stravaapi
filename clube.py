#!/usr/bin/env python
# coding: utf-8

# In[91]:


import pandas as pd
import streamlit as st
st.set_page_config(layout="wide")
from dotenv import load_dotenv
import os


# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# In[30]:


import paramiko
from scp import SCPClient
import pandas as pd



# Configurações do servidor remoto
host = "145.223.30.123"
port = 22  # Porta SSH padrão
username = "root"
password = os.getenv('SSH_PASS')  # Pegar a variável do .env
# password = "Marcio@aynrand7"
remote_path = "/root/play/stravaapi/atividades_unicas.csv"
local_path = "atividades_unicas.csv"

def download_csv_via_scp():
    # Cria o cliente SSH
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # Conecta ao servidor
        ssh.connect(host, port=port, username=username, password=password)

        # Cria o cliente SCP
        with SCPClient(ssh.get_transport()) as scp:
            print("Baixando arquivo...")
            scp.get(remote_path, local_path)  # Baixa o arquivo
            print(f"Arquivo baixado para {local_path}")
    except Exception as e:
        print(f"Erro ao transferir arquivo: {e}")
    finally:
        ssh.close()

def process_csv():
    try:
        # Lê o arquivo CSV local
        df = pd.read_csv(local_path)
        # Exibe as primeiras linhas do DataFrame
    except Exception as e:
        print(f"Erro ao processar o arquivo CSV: {e}")

# Executa as funções
download_csv_via_scp()
process_csv()


# In[35]:


# df_strava = pd.read_csv('unique_activities_old.csv')
df_strava = pd.read_csv('atividades_unicas.csv')
df_strava['athlete.fullname'] = df_strava['firstname'] + ' ' + df_strava['lastname']
df_strava['moving_time_minutes'] = round(df_strava['moving_time']/60, 2)


# In[94]:


from datetime import datetime, timedelta


cols = ['athlete.fullname','name', 'type', 'distance',   
         'data_atual', 'distance_km', 'pace_real','moving_time_minutes'
       ]
# df_strava['moving_time_minutes'] = round(df_strava['moving_time']/60, 2)

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
runs = corridas.loc[corridas['type'] == 'Run' ]

# Agrupar por atleta e agregar as datas em uma lista
grouped = runs.groupby("athlete.fullname").agg(
    total_quilometros=("distance", lambda x: round(x.sum() / 1000, 2)),
    
    tempo_total=("moving_time_minutes", "sum"),
    datas=("data_atual", lambda x: list(x))
).reset_index()

# Definir o intervalo de datas
start_date = datetime.strptime('2025-01-09', '%Y-%m-%d')
end_date = datetime.strptime('2025-01-18', '%Y-%m-%d')

# Gerar uma lista de datas no intervalo
date_range = [(start_date + timedelta(days=i)).strftime('%d-%m-%y') for i in range((end_date - start_date).days + 1)]

# Verificar se cada data no intervalo está presente e criar colunas
for date in date_range:
    grouped[date] = grouped['datas'].apply(
        lambda x: '🏃🏻‍♂️' if date in [datetime.strptime(d, '%Y-%m-%d').strftime('%d-%m-%y') for d in x] else ''
    )

# Verificar se o tempo_total de cada dia é maior que 30 minutos e adicionar 'tempo ok'
for date in date_range:
    grouped[date] = grouped.apply(
        lambda row: f"{row[date]} ⏱️" if row[date] == '🏃🏻‍♂️' and row['tempo_total'] > 30 else row[date], axis=1
    )

# Remover a coluna 'datas'
grouped = grouped.drop(columns=['datas'])
# Ordenar por total_quilometros em ordem decrescente
grouped = grouped.sort_values(by='total_quilometros', ascending=False)

# Redefinir o índice e adicionar uma coluna de numeração começando de 1
grouped.reset_index(drop=True, inplace=True)
grouped.index += 1
grouped.index.name = 'Classificação'


# Renomear a coluna 'total_quilometros' para 'Distância'
grouped.rename(columns={'total_quilometros': 'Distância'}, inplace=True)
grouped.rename(columns={'athlete.fullname': 'Atleta'}, inplace=True)
grouped.rename(columns={'tempo_total': 'Tempo Total'}, inplace=True)



pontuacao_participantes = grouped

st.logo('logo.svg', size='large')
st.image('logo1.png', width=200)
# st.subheader('_Play Distance_ - Desafio 10 dias')
pontuacao_participantes




# In[ ]:





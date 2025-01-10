import pandas as pd
import streamlit as st
st.set_page_config(layout="wide")
from dotenv import load_dotenv
import os
import paramiko
from scp import SCPClient
from datetime import datetime, timedelta

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Configurações do servidor remoto
host = "145.223.30.123"
port = 22  # Porta SSH padrão
username = "root"
password = os.getenv('SSH_PASS')  # Pegar a variável do .env
remote_path = "/root/atividades_unicas.csv"
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
        return df
    except Exception as e:
        print(f"Erro ao processar o arquivo CSV: {e}")
        return pd.DataFrame()

# Executa as funções
download_csv_via_scp()
df_strava = process_csv()

if df_strava.empty:
    print("Erro ao carregar o arquivo CSV.")
else:
    # Processamento dos dados do CSV
    df_strava['athlete.fullname'] = df_strava['firstname'] + ' ' + df_strava['lastname']
    df_strava['moving_time_minutes'] = round(df_strava['moving_time'] / 60, 2)
    df_strava['distance_km'] = round(df_strava['distance'] / 1000, 2)

    # Filtrar os dados pelo data_atual
    filtered_df = df_strava[df_strava['data_atual'] == '2025-01-09']

    # Função para ajustar os valores de distance
    def adjust_distances(group):
        total_distance = group['distance_km'].sum()
        if total_distance > 8:
            group['distance_km'] = group['distance_km'] * (8 / total_distance)
        return group

    # Aplicar a função de ajuste ao DataFrame agrupado por firstname
    adjusted_df = filtered_df.groupby('athlete.fullname').apply(adjust_distances).reset_index(drop=True)

    # Atualizar o DataFrame original com os novos valores de distance
    for index, row in adjusted_df.iterrows():
        df_strava.loc[(df_strava['data_atual'] == '2025-01-09') & 
                      (df_strava['athlete.fullname'] == row['athlete.fullname']), 'distance_km'] = row['distance_km']

    # Função para converter velocidade em pace
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

    # Filtrar o DataFrame para a data específica
    data_especifica = '2025-01-09'
    df_filtrado = df_strava[df_strava['data_atual'] == data_especifica]

    # Calcular a soma de distance_km para a data específica
    soma_distance_km = df_filtrado['distance_km'].sum()

    # Se a soma ultrapassar 8 km, ajustar os valores de distance_km proporcionalmente
    if soma_distance_km > 8:
        fator_ajuste = 8 / soma_distance_km
        df_strava.loc[df_strava['data_atual'] == data_especifica, 'distance_km'] *= fator_ajuste

    cols = ['athlete.fullname', 'name', 'type', 'distance', 'data_atual', 'distance_km', 'pace_real', 'moving_time_minutes', 'total_elevation_gain']
    corridas = df_strava[cols]
    runs = corridas.loc[corridas['type'] == 'Run']

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

    # Renomear colunas
    grouped.rename(columns={'total_quilometros': 'Distância', 'athlete.fullname': 'Atleta', 'tempo_total': 'Tempo Total'}, inplace=True)

    # Exibir os resultados no Streamlit
    st.logo('logo.svg', size='large')
    st.image('logo1.png', width=200)
    st.write("_Play Distance_ - Desafio 10 dias")
    st.dataframe(grouped)
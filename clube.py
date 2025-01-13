import pandas as pd
import streamlit as st
st.set_page_config(layout="wide")
from dotenv import load_dotenv
import os
import paramiko
from scp import SCPClient
from datetime import datetime, timedelta
import plotly.express as px



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
        df = pd.read_csv(local_path, dtype={
            'firstname': 'object',
            'lastname': 'object',
            'name': 'object',
            'distance': 'float64',
            'moving_time': 'float64',
            'elapsed_time': 'float64',
            'total_elevation_gain': 'float64',
            'type': 'object',
            'sport_type': 'object',
            'data_atual': 'object'
        })
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
    
    # Função para ajustar os valores de distance_km
    def adjust_distances(group):
        total_distance = group['distance_km'].sum()
        if total_distance > 8:
            group['distance_km'] = 8
        return group

    # Aplicar a função de ajuste ao DataFrame agrupado por athlete.fullname
    adjusted_df = filtered_df.groupby('athlete.fullname').apply(adjust_distances).reset_index(drop=True)

    # Atualizar o DataFrame original com os novos valores de distance_km
    for index, row in adjusted_df.iterrows():
        athlete_mask = (df_strava['data_atual'] == '2025-01-09') & (df_strava['athlete.fullname'] == row['athlete.fullname'])
        df_strava.loc[athlete_mask, 'distance_km'] = row['distance_km']

    # Recalcular a soma de distance_km para garantir que não ultrapasse 8 km no total
    for athlete in df_strava['athlete.fullname'].unique():
        athlete_mask = (df_strava['data_atual'] == '2025-01-09') & (df_strava['athlete.fullname'] == athlete)
        athlete_total_distance = df_strava.loc[athlete_mask, 'distance_km'].sum()
        
        if athlete_total_distance > 8:
            df_strava.loc[athlete_mask, 'distance_km'] *= 8 / athlete_total_distance

    # Função para converter velocidade em pace
    def kmh_to_min_km(speed_kmh):
        if speed_kmh > 0:  # Evitar divisão por zero
            pace = 60 / speed_kmh
            minutes = int(pace)
            seconds = int((pace - minutes) * 60)
            return f"{minutes}:{seconds:02d} min/km"
        else:
            return None  # Retorna None para velocidades inválidas

    df_strava['avg_speed_kmh'] = df_strava['distance_km'] / (df_strava['moving_time_minutes'] / 60)
    df_strava['avg_speed_kmh'] = pd.to_numeric(df_strava['avg_speed_kmh'], errors='coerce')
    df_strava['pace_real'] = df_strava['avg_speed_kmh'].apply(kmh_to_min_km)
    
    cols = ['athlete.fullname', 'name', 'type', 'distance', 'data_atual', 'distance_km', 'pace_real', 'moving_time_minutes', 'total_elevation_gain']
    corridas = df_strava[cols]
    runs = corridas.loc[corridas['type'] == 'Run']

    # Agrupar por atleta e agregar as datas em uma lista
    grouped = runs.groupby("athlete.fullname").agg(
        total_quilometros=("distance_km", "sum"),
        tempo_total=("moving_time_minutes", "sum"),
        datas=("data_atual", lambda x: list(x)),
        
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
    
    grouped
    grouped = grouped.sort_values(by="Distância", ascending=False)
    
# Gerar o gráfico horizontal
fig = px.bar(
    grouped,
    x="Distância",          # Valores do eixo X (horizontal)
    y="Atleta",             # Valores do eixo Y (vertical)
    orientation="h",        # Define a orientação horizontal
    # title="Ranking de Atletas - Desafio 10 dias",
    labels={"Distância": "Distância (km)", "Atleta": "Atletas"},    # Mostrar os valores no gráfico
    color="Atleta",         # Diferenciar as barras por cor com base nos atletas
    color_discrete_sequence=px.colors.qualitative.Set2,  # Escolher uma paleta de cores
)

# Ajustar o layout para aumentar a altura
fig.update_layout(
    height=1000, # Define a altura do gráfico
    yaxis=dict(
        title="Atletas",
        categoryorder="total ascending",  # Inverter a ordem do eixo Y
    ),
    xaxis=dict(title="Distância (km)"),
    showlegend=False,
    margin=dict(l=0, r=0, t=0, b=0),  # Remove todas as margens
)

st.plotly_chart(fig, use_container_width=True)

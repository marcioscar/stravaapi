import pandas as pd
import streamlit as st
import plotly.express as px

df = pd.read_csv('play.csv', sep=';', decimal=',')
st.set_page_config(layout="wide", page_title="Play Distance", page_icon="🏃‍♂️")


feminino = df[df['Sexo'] == 'F'].sort_values(by='KM', ascending=False)
masculinos = df[df['Sexo'] == 'M'].sort_values(by='KM', ascending=False)

max_km = feminino["KM"].max()
feminino["Diferenca_KM"] = max_km - df["KM"]



feminino.reset_index(drop=True, inplace=True)
feminino.index += 1
feminino.index.name = 'Classificação'

masculinos.reset_index(drop=True, inplace=True)
masculinos.index += 1
masculinos.index.name = 'Classificação'


# Exibir os resultados no Streamlit
st.logo('logo.svg', size='large')
st.image('logo1.png', width=200)
st.write("_Play Distance_ - Desafio 10 dias")
feminino = feminino[['Nome', 'KM']]
# feminino = feminino[['Nome', 'KM', 'Diferença_KM']]

masculinos = masculinos[['Nome', 'KM']]
st.subheader("Classificação Mulheres")
st.dataframe(feminino, use_container_width=True)

st.divider()
st.subheader("Classificação Homens")
st.dataframe(masculinos, use_container_width=True)




config = {
    'displayModeBar': False  # Remove a barra de ferramentas
}
fem = px.bar(
    feminino,
    x="KM",          # Valores do eixo X (horizontal)
    y="Nome",             # Valores do eixo Y (vertical)
    orientation="h",        # Define a orientação horizontal
    # title="Ranking de Atletas - Desafio 10 dias",
    labels={"KM": "Distância (km)", "Nome": "Atletas"},    # Mostrar os valores no gráfico
    color="Nome",         # Diferenciar as barras por cor com base nos atletas
    color_discrete_sequence=px.colors.qualitative.Set2,  # Escolher uma paleta de cores
)

# Ajustar o layout para aumentar a altura
fem.update_layout(

    height=1000, # Define a altura do gráfico
    yaxis=dict(
        title="Nome",
        categoryorder="total ascending",  # Inverter a ordem do eixo Y
    ),
    xaxis=dict(title="Distância (km)"),
    showlegend=False,
    margin=dict(l=0, r=0, t=0, b=0), 
      
)


st.subheader("Gráfico Mulheres")
st.plotly_chart(fem, use_container_width=True, config=config)

masc = px.bar(
    masculinos,
    x="KM",          # Valores do eixo X (horizontal)
    y="Nome",             # Valores do eixo Y (vertical)
    orientation="h",        # Define a orientação horizontal
    # title="Ranking de Atletas - Desafio 10 dias",
    labels={"KM": "Distância (km)", "Nome": "Atletas"},    # Mostrar os valores no gráfico
    color="Nome",         # Diferenciar as barras por cor com base nos atletas
    color_discrete_sequence=px.colors.qualitative.Set2,  # Escolher uma paleta de cores
)

# Ajustar o layout para aumentar a altura
masc.update_layout(
    height=1000, # Define a altura do gráfico
    yaxis=dict(
        title="Nome",
        categoryorder="total ascending",  # Inverter a ordem do eixo Y
    ),
    xaxis=dict(title="Distância (km)"),
    showlegend=False,
    margin=dict(l=0, r=0, t=0, b=0),  # Remove todas as margens
)
st.subheader("Gráfico Homens")
st.plotly_chart(masc, use_container_width=True, config=config)



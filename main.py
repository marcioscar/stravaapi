import csv
from datetime import datetime
import os
from pathlib import Path
import pandas as pd
from datetime import datetime

from src.api_methods import get_methods
from src.api_methods import authorize
from src.data_preprocessing import main as data_prep


def main():
    token:str = authorize.get_acces_token()
    dfs_to_concat = []

    data:dict = get_methods.access_club_data(token, params={
            'per_page': 200,  
        })
    cur_df = data_prep.preprocess_data(data)

# Adiciona a data atual como uma nova coluna no DataFrame
    current_date = datetime.now().strftime('%Y-%m-%d')  # Formata a data como AAAA-MM-DD
    cur_df['data_atual'] = current_date  # Adiciona a data ao DataFrame

    dfs_to_concat.append(cur_df)
      
    
    
    #atvidades do usuario    
    # while True:
    #     data:dict = get_methods.access_activity_data(token, params={
    #         'per_page': 200,
    #         'page': page_number,
    #     })
    #     page_number += 1
    #     cur_df = data_prep.preprocess_data(data)
    #     dfs_to_concat.append(cur_df)
    #     if len(data) == 0:
    #         break
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    df = pd.concat(dfs_to_concat, ignore_index=True)
    
    csv_file_1 = 'club_activities.csv'
    file_exists = os.path.isfile(csv_file_1)
    with open(csv_file_1, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow([
                'firstname', 'lastname', 'name', 'distance', 'moving_time',
                'elapsed_time', 'total_elevation_gain', 'type', 'sport_type', 'data_atual'
            ])
        for _, activity in df.iterrows():
            firstname = activity.get('athlete.firstname', '')
            lastname = activity.get('athlete.lastname', '')
            name = activity.get('name', '')
            distance = activity.get('distance', 0)
            moving_time = activity.get('moving_time', 0)
            elapsed_time = activity.get('elapsed_time', 0)
            total_elevation_gain = activity.get('total_elevation_gain', 0)
            activity_type = activity.get('type', '')
            sport_type = activity.get('sport_type', '')
            data_atual = activity.get('data_atual', '')
            writer.writerow([
                firstname,
                lastname,
                name,
                distance,
                moving_time,
                elapsed_time,
                total_elevation_gain,
                activity_type,
                sport_type,
                data_atual
            ])
    csv_file_2 = 'atividades_unicas.csv'
    df = pd.read_csv(csv_file_1)
     # Remove registros duplicados considerando os campos especificados
    filtered_df = df.drop_duplicates(subset=[
        'firstname', 'lastname', 'name', 'distance', 'moving_time',
        'elapsed_time', 'total_elevation_gain', 'type', 'sport_type'
    ])
    # Filtrar registros após a data especificada
    atividades_unicas_data = filtered_df[filtered_df['data_atual'] > '2025-01-07']
    
    # Salva o DataFrame filtrado em um novo CSV
    atividades_unicas_data.to_csv(csv_file_2, index=False)

    print(f'Atividades salvas em: {csv_file_1}')
    print(f'Atividades filtradas e salvas em: {csv_file_2}')





    # df.to_csv(Path('data', f'my_activity_data={timestamp}.csv'), index=False)
    

if __name__ == '__main__':
    main()
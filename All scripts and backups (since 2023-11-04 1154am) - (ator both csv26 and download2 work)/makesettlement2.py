import pandas as pd
import os
from itertools import product

def create_csv_for_all_settlements(all_settlements, base_url, save_dir, data, religion_mapping, first_year, last_year):
    for settlement in all_settlements:
        file_name = f"{settlement}_{first_year}-{last_year}_all_religions.csv"
        file_path = os.path.join(save_dir, file_name)

        with open(file_path, 'w') as file:
            file.write("URL\n")
            for religion in religion_mapping.values():
                for year in range(first_year, last_year + 1):
                    for state in data['state'].dropna().unique():
                        # Creating a properly encoded URL for the settlement name
                        url_settlement = settlement.replace(' ', '%20').replace('-', '%20').title()
                        url = f"{base_url}{url_settlement}/{religion}/{year}/{state}/0001.jpg\n"
                        file.write(url)

# Settings
excel_path = 'library.xlsx'  # Make sure to place the 'library.xlsx' in the current working directory
data = pd.read_excel(excel_path)
all_settlements = data['settlement'].dropna().unique()
base_url = "https://maticneknjige.org.rs/wp-content/uploads/Skenovi/"
save_dir = 'settlement_csvs'
os.makedirs(save_dir, exist_ok=True)

religion_mapping = {
    'c': 'rimokatolici',
    'e': 'evangelisti',
    'f': 'reformati',
    'g': 'grkokatolici',
    'j': 'jevreji',
    'n': 'nazareni',
    'r': 'pravoslavni_rumuni',
    's': 'pravoslavni_srbi'
}

first_year = 1800
last_year = 1896

# Create CSV for each settlement
create_csv_for_all_settlements(all_settlements, base_url, save_dir, data, religion_mapping, first_year, last_year)

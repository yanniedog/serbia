import pandas as pd
import os
from itertools import product
def get_religions_input():
    print('Please enter the religions to include, using the corresponding letters:')
    print('[c] rimokatolici (Roman Catholic)')
    print('[e] evangelisti (Evangelists)')
    print('[f] reformati')
    print('[j] jevreji (Jewish)')
    print('[n] nazareni (Nazarenes)')
    print('[r] pravoslavni_rumuni (Orthodox Romanians)')
    print('[s] pravoslavni_srbi (Orthodox Serbs)')
    input_str = input('Enter the letters for the religions, separated by space ("c r s"), or "a" for all:  ')
    return input_str
def select_settlements(settlements):
    print("Available settlements:")
    for i, settlement in enumerate(settlements, start=1):
        print(f"[{i}] {settlement}")
    indices = input("Enter the number(s) for the settlement(s) you want to create CSVs for (e.g., '1 3 5'): ")
    selected_indices = [int(index) for index in indices.split()]
    return [settlements[i - 1] for i in selected_indices]
excel_path = '/home/pi/serbia/excel/library.xlsx'
data = pd.read_excel(excel_path)
all_settlements = data['settlement'].dropna().unique()
selected_settlements = select_settlements(all_settlements)
base_url = "https://maticneknjige.org.rs/wp-content/uploads/Skenovi/"
save_dir = 'settlement_csvs'
os.makedirs(save_dir, exist_ok=True)
religion_mapping = {
    'c': 'rimokatolici',
    'e': 'evangelisti',
    'f': 'reformati',
    'j': 'jevreji',
    'n': 'nazareni',
    'r': 'pravoslavni_rumuni',
    's': 'pravoslavni_srbi'
}
for settlement in selected_settlements:
    print(f"Generating CSV for settlement: {settlement}")
    first_year = int(input("Enter the first year [default: 1756]: ") or "1756")
    last_year = int(input("Enter the last year [default: 1895]: ") or "1895")
    religion_input = get_religions_input()
    selected_religions = list(religion_mapping.values()) if "a" in religion_input else [religion_mapping[letter] for letter in religion_input if letter in religion_mapping]
    years = range(first_year, last_year + 1)
    religions = [religion for religion in data['religion'].dropna().unique() if religion in selected_religions]
    states = data['state'].dropna().unique()
    image_nos = data['image_no'].dropna().astype(int).apply(lambda x: f"{x:03}").unique()
    file_name = f"{settlement}.csv"
    file_path = os.path.join(save_dir, file_name)
    with open(file_path, 'w') as file:
        file.write("URL\n")  # Correct this line
        for religion, year, state, image_no in product(religions, years, states, image_nos):
            url = f"{base_url}{settlement.replace('-', '%20').title()}/{religion}/{year}/{state}/{image_no}.jpg\n"
            file.write(url)
    print(f"CSV file created for settlement: {settlement}")
print("All CSV files have been created.")

from tabulate import tabulate

def display_settlements_in_columns(settlements_list):
    # Split the settlements into groups for each column
    num_columns = 4
    split_settlements = [settlements_list[i:i + num_columns] for i in range(0, len(settlements_list), num_columns)]
    # Use tabulate to create a columnar table
    print(tabulate(split_settlements, tablefmt="plain"))


from tabulate import tabulate

def display_settlements_in_columns(settlements_list):
    # Split the settlements into groups for each column
    num_columns = 4
    split_settlements = [settlements_list[i:i + num_columns] for i in range(0, len(settlements_list), num_columns)]
    # Use tabulate to create a columnar table
    print(tabulate(split_settlements, tablefmt="plain"))

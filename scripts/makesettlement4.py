import pandas as pd
import os
from itertools import product

def get_religions_input():
    print('Please enter the religions to include, using the corresponding letters:')
    print('[c] rimokatolici (Roman Catholic)')
    print('[e] evangelisti (Evangelists)')
    print('[f] reformati')
    print('[g] grkokatolici (Greek Catholic)')
    print('[j] jevreji (Jewish)')
    print('[n] nazareni (Nazarenes)')
    print('[r] pravoslavni_rumuni (Orthodox Romanians)')
    print('[s] pravoslavni_srbi (Orthodox Serbs)')
    input_str = input('Enter the letters for the religions, separated by space ("c r s"), or "a" for all: ')
    return input_str

def select_settlement(all_settlements):
    print("Available settlements:")
    for i, settlement in enumerate(all_settlements, start=1):
        print(f"[{i}] {settlement}")
    index = input("Enter the number for the settlement you want to create a CSV for (e.g., '1'): ")
    selected_index = int(index) - 1
    return all_settlements[selected_index]

def create_csv_for_selected_settlement(base_url, save_dir, data, religion_mapping, num_digits, num_filenames, first_year, last_year, religion_input, selected_settlement):
    print(f"Generating CSV for settlement: {selected_settlement}")

    if "a" in religion_input:
        selected_religions = list(religion_mapping.values())
        file_religions_part = "all"
    else:
        selected_religions = [religion_mapping[letter] for letter in religion_input if letter in religion_mapping]
        file_religions_part = "_".join(selected_religions)

    years = range(first_year, last_year + 1)
    religions = [religion for religion in data['religion'].dropna().unique() if religion in selected_religions]
    states = data['state'].dropna().unique()

    file_name = f"{selected_settlement}_{first_year}-{last_year}_{file_religions_part}.csv"
    file_path = os.path.join(save_dir, file_name)

    with open(file_path, 'w') as file:
        file.write("URL\n")
        for religion, year, state in product(religions, years, states):
            for i in range(1, num_filenames + 1):
                url_settlement = selected_settlement.replace(' ', '%20').replace('-', '%20').title()
                file_number = str(i).zfill(num_digits)
                url = f"{base_url}{url_settlement}/{religion}/{year}/{state}/{file_number}.jpg\n"
                file.write(url)

    print(f"CSV file created for settlement: {selected_settlement}")

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

# Get user input for the number of digits and filenames to generate
num_digits = int(input("Enter the number of digits each filename should have (e.g., 3 for 001.jpg or 4 for 0001.jpg): "))
num_filenames = int(input("Enter the number of filenames to generate for each state directory: "))

while True:
    first_year = int(input("Enter the first year [default: 1800]: ") or "1800")
    last_year = int(input("Enter the last year [default: 1896]: ") or "1896")
    religion_input = get_religions_input()
    selected_settlement = select_settlement(all_settlements)

    # Create CSV for the selected settlement
    create_csv_for_selected_settlement(base_url, save_dir, data, religion_mapping, num_digits, num_filenames, first_year, last_year, religion_input, selected_settlement)

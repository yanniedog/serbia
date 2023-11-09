
import configparser
config = configparser.ConfigParser()
config.read('/home/pi/serbia/config/serbia.cfg')
working_directory = config['DEFAULT']['csv_in']
import os

# Get the current working directory
working_directory = working_directory

# Create directories named 'settlement_csvs41' through 'settlement_csvs100' in the working directory
for i in range(41, 250):
    dir_name = f'settlement_csvs{i}'
    dir_path = os.path.join(working_directory, dir_name)
    os.makedirs(dir_path, exist_ok=True)

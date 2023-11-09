import os
import time
import pandas as pd
import requests
from random import shuffle
from urllib.parse import urlparse, unquote
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from colorama import Fore, Back, Style, init
from datetime import datetime
import sys
import csv
import configparser
import traceback
import random
import numpy as np
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from session_screen_output import print_colored_message, print_status_with_color, print_exception_with_color

# Read configuration file
config = configparser.ConfigParser()
config.read('/home/pi/serbia/config/serbia.cfg')

# Constants from configuration file
USERNAME = config['DEFAULT']['username']
PASSWORD = config['DEFAULT']['password']
CSV_DIRECTORY_BASE = config['DEFAULT']['csv_directory']
LOCAL_IMAGE_BASE_PATH_BASE = config['DEFAULT']['local_image_base_path']
LOG_FILE_PATH_BASE = config['DEFAULT']['log_file_path']
COMPLETED_CSV_DIRECTORY_BASE = config['DEFAULT']['completed_csv_directory']
OVERALL_LOG_PATH = config['DEFAULT']['overall_log_path']
GECKODRIVER_PATH = config['DEFAULT']['geckodriver_path']
BROWSER_OPTIONS = config['DEFAULT']['browser_options'].split()
CHUNK_SIZE = config.getint('DEFAULT', 'chunk_size')
MAX_RESTARTS = config.getint('DEFAULT', 'max_restarts')
LOGIN_URL = config['DEFAULT']['login_url']
SELENIUM_TIMEOUT = config.getint('DEFAULT', 'selenium_timeout', fallback=10)

# Helper function to print messages with session number
def print_with_session_number(session_number, message):
    print_colored_message(f"(#{session_number}): {message}")

# Helper function to print exceptions with traceback
def print_exception(session_number, e):
    print_exception_with_color(session_number, e)

# Function to handle image downloading
def handle_image(url, local_path, session, session_number, CHUNK_SIZE):
    try:
        # Set up retry strategy for better resilience
        retries = Retry(total=5,
                        backoff_factor=1,
                        status_forcelist=[429, 500, 502, 503, 504],
                        allowed_methods=["HEAD", "GET"])  # Updated line here
        session.mount('https://', HTTPAdapter(max_retries=retries))

        # Correct the local path by ensuring it is absolute and does not start with '//'
        if local_path.startswith('//'):
            local_path = local_path[1:]  # Remove one of the slashes
        
        # Ensure the directory for the local_path exists
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        # Attempt to get the headers with a timeout to prevent hanging
        head = session.head(url, timeout=10)
        if head.status_code == 200:
            print_with_session_number(session_number, f"Image exists: {url}")

            # Download the image in chunks
            with open(local_path, 'wb') as out_file:
                response = session.get(url, stream=True, timeout=10)
                for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                    out_file.write(chunk)
            print_with_session_number(session_number, f"Image downloaded: {url}")
            return True
        else:
            # If the image is not found or another HTTP error occurred
            return False
    except requests.RequestException as e:
        print_exception(session_number, e)
        return False

# Function to ensure directory exists
def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

# Function to initialize the overall log file
def init_overall_log(log_file_path, session_number):
    ensure_dir(log_file_path)
    if not os.path.isfile(log_file_path):
        with open(log_file_path, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                "Original Filename", "Completion Timestamp", "Image Range", "Digit Format",
                "Duplication Status", "Late Start", "Gaps Found", "Total Listed Images",
                "Images Found Locally", "Images Saved", "Session Number",
                "Execution Duration", "Restart Count"
            ])
    print_with_session_number(session_number, f"Initialized overall log file at {log_file_path}")

# Function to parse image numbers and track stats
def parse_image_numbers(df, session_number):
    stats = {
        'smallest_image': None,
        'largest_image': None,
        'digit_format': 'unknown',
        'dup_status': 'nodups',
        'late_start': False,
        'gaps_found': False,
        'total_images': len(df),
        'existing_images': 0,
        'saved_images': 0
    }

    seen_numbers = set()

    for _, row in df.iterrows():
        image_url = row['URL']
        image_number = int(os.path.splitext(os.path.basename(image_url))[0])
        seen_numbers.add(image_number)

    if seen_numbers:
        stats['smallest_image'] = min(seen_numbers)
        stats['largest_image'] = max(seen_numbers)

        # Detecting image number format, duplicates, and gaps
        stats['digit_format'] = '3n' if all(len(str(num)) == 3 for num in seen_numbers) else '4n' if all(len(str(num)) == 4 for num in seen_numbers) else 'mixed'
        stats['dup_status'] = 'dups' if len(seen_numbers) < stats['total_images'] else 'nodups'
        stats['late_start'] = min(seen_numbers) != 1
        stats['gaps_found'] = len(seen_numbers) != stats['largest_image'] - stats['smallest_image'] + 1

    print_with_session_number(session_number, f"Stats parsed: {stats}")
    return stats

# Function to rename and log completed CSV
def rename_completed_csv(original_csv_path, completed_csv_directory, stats, session_number, restart_count, duration):
    filename, ext = os.path.splitext(os.path.basename(original_csv_path))
    new_filename = f"{filename}_{session_number}_done.csv"
    os.rename(original_csv_path, os.path.join(completed_csv_directory, new_filename))
    print_with_session_number(session_number, f"Renamed CSV: {original_csv_path} to {new_filename}")
    return new_filename

# Function to update status and save CSV, and print a colored concise message
def update_status_and_save_csv(df, csv_path, index, status, session_number):
    status_map = {'Not Found': 'N', 'Downloaded': 'D', 'Exists': 'E'}
    df.at[index, 'Status'] = status_map[status]
    df.to_csv(csv_path, index=False)

    url_parts = urlparse(df.at[index, 'URL'])
    url_path_parts = url_parts.path.split('/')
    settlement, religion, year, state = url_path_parts[-5], url_path_parts[-4], url_path_parts[-3], url_path_parts[-2]

    religion_weight = df.at[index, "religion_weight"]
    year_weight = df.at[index, "year_weight"]
    state_weight = df.at[index, "state_weight"]
    overall_weight = df.at[index, "Weight"]

    print_status_with_color(session_number, f"Row {index} ({settlement}/{religion}/{year}/{state}/{os.path.basename(url_parts.path)}) ", status, religion_weight=religion_weight, year_weight=year_weight, state_weight=state_weight, overall_weight=overall_weight)

# Initialize colorama
init(autoreset=True)

# Function to shuffle DataFrame rows
def shuffle_dataframe(df):
    df = df.sample(frac=1).reset_index(drop=True)
    return df

# Function to update weights
def update_weights(df, index):
    for attr in ['religion', 'year', 'state']:
        weight_column = f"{attr}_weight"
        df.at[index, weight_column] += 1
    return df

# Function to get row weight
def get_row_weight(row):
    weight = 1
    for attr in ['religion', 'year', 'state']:
        weight *= row[f"{attr}_weight"]
    return weight

# Function to process images for a given CSV file with random walk
def process_images(csv_path, session, session_number, CHUNK_SIZE, LOG_FILE_PATH, LOCAL_IMAGE_BASE_PATH):
    all_status_assigned = True
    try:
        df = pd.read_csv(csv_path)
        # Initialize status and weights if not present
        if 'Status' not in df.columns:
            df['Status'] = None  # Initialize all rows with no status
        for attr in ['religion', 'year', 'state']:
            weight_column = f"{attr}_weight"
            if weight_column not in df.columns:
                df[weight_column] = 1
        if 'Weight' not in df.columns:
            df['Weight'] = df.apply(get_row_weight, axis=1)

        while df['Status'].isna().sum() > 0:
            # Select a row with a positive bias towards higher weights, but only from those that haven't been processed yet
            unprocessed_df = df[df['Status'].isna()]
            selected_row = unprocessed_df.sample(weights='Weight').iloc[0]
            selected_index = selected_row.name  # 'name' property holds the original index of the row

            image_url = selected_row['URL']
            local_image_path = os.path.join(LOCAL_IMAGE_BASE_PATH, *unquote(urlparse(image_url).path).split('/')[1:])

            # Check if the image already exists and skip downloading if it does
            if os.path.exists(local_image_path):
                print_with_session_number(session_number, f"Image already exists: {local_image_path}")
                df.at[selected_index, 'Status'] = 'E'  # Exists
            else:
                # Download the image if it does not exist
                if handle_image(image_url, local_image_path, session, session_number, CHUNK_SIZE):
                    df.at[selected_index, 'Status'] = 'D'  # Downloaded
                else:
                    df.at[selected_index, 'Status'] = 'N'  # Not Found
                    log_image_not_found(image_url, LOG_FILE_PATH, session_number)

            # Update the weights
            df = update_weights(df, selected_index)

            # Save the DataFrame to CSV after each row is processed
            df.to_csv(csv_path, index=False)

        all_status_assigned = df['Status'].isna().sum() == 0

    except pd.errors.EmptyDataError:
        print_with_session_number(session_number, "CSV is empty or corrupted.")
    except Exception as e:
        print_exception(session_number, e)

    # Parse image numbers and track stats after processing is complete
    stats = parse_image_numbers(df, session_number)
    return stats, all_status_assigned

# Function to start the browser in headless mode
def start_browser():
    service = Service(GECKODRIVER_PATH)
    options = Options()
    for option in BROWSER_OPTIONS:
        options.add_argument(option)
    options.add_argument('-headless')
    browser = webdriver.Firefox(service=service, options=options)
    return browser

# Function to write to overall log
def write_to_overall_log(log_file_path, data, session_number):
    with open(log_file_path, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(data)
    print_with_session_number(session_number, f"Wrote overall log entry: {data}")

# Function to log image not found
def log_image_not_found(image_url, log_file_path, session_number):
    ensure_dir(log_file_path)
    with open(log_file_path, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([image_url])
    # print_with_session_number(session_number, f"Logged image not found: {image_url}")

# Entry point of the script
if __name__ == "__main__":
    session_number = sys.argv[1] if len(sys.argv) > 1 else 'default'
    restart_count = 0

    init_overall_log(OVERALL_LOG_PATH, session_number)
    print_with_session_number(session_number, "Starting main script execution")

    session = requests.Session()
    browser = None

    try:
        browser = start_browser()
        browser.get(LOGIN_URL)
        browser.implicitly_wait(SELENIUM_TIMEOUT)

        username_field = browser.find_element(By.ID, "user_login")
        password_field = browser.find_element(By.ID, "user_pass")
        submit_button = browser.find_element(By.ID, "wp-submit")

        username_field.send_keys(USERNAME)
        password_field.send_keys(PASSWORD)
        submit_button.click()
        time.sleep(5)

        selenium_cookies = browser.get_cookies()
        for cookie in selenium_cookies:
            session.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'])

        print_with_session_number(session_number, "Logged in and set cookies for session")


        CSV_DIRECTORY = f'{CSV_DIRECTORY_BASE}{session_number}'
        LOCAL_IMAGE_BASE_PATH = os.path.join(LOCAL_IMAGE_BASE_PATH_BASE, f'downloaded_images{session_number}')
        LOG_FILE_PATH = f'{LOG_FILE_PATH_BASE}{session_number}/images_not_found.csv'
        COMPLETED_CSV_DIRECTORY = f'{COMPLETED_CSV_DIRECTORY_BASE}{session_number}'

        ensure_dir(LOG_FILE_PATH)
        ensure_dir(LOCAL_IMAGE_BASE_PATH)
        ensure_dir(COMPLETED_CSV_DIRECTORY)

        csv_files = sorted([f for f in os.listdir(CSV_DIRECTORY) if f.endswith('.csv')])

        for csv_file in csv_files:
            csv_path = os.path.join(CSV_DIRECTORY, csv_file)
            start_time = time.time()
            df, all_status_assigned = process_images(csv_path, session, session_number, CHUNK_SIZE, LOG_FILE_PATH, LOCAL_IMAGE_BASE_PATH)
            duration = int(time.time() - start_time)
            if all_status_assigned:
                renamed_csv = rename_completed_csv(csv_path, COMPLETED_CSV_DIRECTORY, stats, session_number, restart_count, duration)
                write_to_overall_log(OVERALL_LOG_PATH, [
                    renamed_csv, datetime.now().strftime('%Y%m%d__%H%M%S'), stats['smallest_image'],
                    stats['largest_image'], stats['digit_format'], stats['dup_status'], stats['late_start'],
                    stats['gaps_found'], stats['total_images'], stats['existing_images'], stats['saved_images'],
                    session_number, duration, restart_count
                ], session_number)
            else:
                print_with_session_number(session_number, f"CSV not completed: {csv_path}")

    except Exception as e:
        print_exception(session_number, e)
    finally:
        if browser:
            browser.quit()

    print_with_session_number(session_number, "Finished main script execution")

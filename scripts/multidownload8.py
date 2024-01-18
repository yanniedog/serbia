import os
import time
import json
import pandas as pd
import requests
import csv
import re
import glob
from requests.exceptions import ConnectionError, Timeout, RequestException
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from datetime import datetime
import shutil
from urllib.parse import urlparse, unquote
import sys

# Constants
LOGIN_URL = "https://maticneknjige.org.rs/wp-login.php"
CHUNK_SIZE = 32768  # Chunk size set to 32 KB
MAX_FAILS = 1  # Maximum number of consecutive fails before skipping to next 'state'
MIN_FREE_SPACE_MB = 500  # Minimum free space required in MB to continue downloads
RETRY_DELAYS = [1, 2, 4, 8, 16, 32, 64]  # Exponential backoff retry delays in seconds

# Set the paths for CSV files, logs, and downloaded images
CSV_FILE_PATH_TEMPLATE = "/home/pi/serbia/excel/settlement_csvs{session_number}"
OVERALL_LOG_PATH_TEMPLATE = "/home/pi/serbia/logs{session_number}"
DOWNLOAD_PATH_TEMPLATE = "/home/pi/serbia/excel/downloaded_images{session_number}"
COMPLETED_CSV_PATH_TEMPLATE = "/home/pi/serbia/completed_csvs{session_number}"

# Paths
SESSION_DATA_PATH = "/home/pi/session_data"  # Path to save session data for persistence

# Ensure session data directory exists
os.makedirs(SESSION_DATA_PATH, exist_ok=True)

# Function to check if there is enough disk space to proceed
def check_disk_space(required_space_mb, path="/"):
    total, used, free = shutil.disk_usage(path)
    free_mb = free // (2**20)
    if free_mb < required_space_mb:
        raise Exception(f"Insufficient disk space: Only {free_mb} MB free, but {required_space_mb} MB is required.")

# Function to save session state
def save_session_state(session_number, state_data):
    state_file_path = os.path.join(SESSION_DATA_PATH, f"session_{session_number}_state.json")
    with open(state_file_path, 'w') as state_file:
        json.dump(state_data, state_file)

# Function to load session state
def load_session_state(session_number):
    state_file_path = os.path.join(SESSION_DATA_PATH, f"session_{session_number}_state.json")
    if os.path.exists(state_file_path):
        with open(state_file_path, 'r') as state_file:
            return json.load(state_file)
    return {}

# Function to ensure directory exists
def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

# Function to log image not found
def log_image_not_found(log_file_path, url):
    with open(log_file_path, 'a') as log_file:
        log_file.write(f"{datetime.now().strftime('%Y%m%d-%H%M%S')},{url}\n")

# Exponential backoff function
def backoff(retry_num):
    time.sleep(RETRY_DELAYS[min(retry_num, len(RETRY_DELAYS)-1)])

# Function to initialize Selenium browser in headless mode
def init_browser():
    options = Options()
    options.add_argument("--headless")
    service = Service('/usr/local/bin/geckodriver')  # Update the path to your geckodriver
    return webdriver.Firefox(options=options, service=service)

# Define a function for updating the overall log
def update_overall_log(log_path, session_info):
    with open(log_path, 'a', newline='', encoding='utf-8') as log_file:
        log_writer = csv.writer(log_file)
        log_writer.writerow(session_info)

# Function to check image existence with session
def check_image_with_session(url, session):
    retry_num = 0
    while True:
        try:
            response = session.head(url, timeout=10)
            return response.status_code == 200
        except (ConnectionError, Timeout) as e:
            if retry_num == len(RETRY_DELAYS):
                print(f"Max retries reached for {url}")
                return False
            print(f"Retrying {url} after error: {e}")
            backoff(retry_num)
            retry_num += 1
        except RequestException as e:
            print(f"Non-retryable exception for {url}: {e}")
            return False

# Function to download and save an image
def save_image(url, session, file_path):
    if not check_disk_space(MIN_FREE_SPACE_MB, "/"):
        print("Not enough disk space to download images.")
        return False

    try:
        with session.get(url, stream=True) as r:
            r.raise_for_status()
            with open(file_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
                    f.write(chunk)
        return True
    except Exception as e:
        print(f"Failed to save image {url}: {e}")
        return False

# The function to process URLs and download images
def process_urls(csv_directory, session_number, session):
    # Load session progress
    progress_data = load_session_state(session_number)
    completed_urls = progress_data.get('completed_urls', set())

    # Look for CSV files in the specified directory
    csv_files = glob.glob(os.path.join(csv_directory, "*.csv"))

    for csv_file_path in csv_files:
        # Load the CSV file containing image URLs
        df = pd.read_csv(csv_file_path)
        # Check if CSV is completely empty which indicates a problem upstream
        if df.empty:
            raise ValueError("The CSV file is empty. Please check the upstream data generation process.")

        # Process each URL in the DataFrame
        for index, row in df.iterrows():
            image_url = row['URL']
            # Skip if URL is already processed
            if image_url in completed_urls:
                continue

            # Check if the image is accessible
            if check_image_with_session(image_url, session):
                # Define the local file path
                local_filename = os.path.join(DOWNLOAD_PATH_TEMPLATE.format(session_number=session_number), os.path.basename(image_url))
                # Ensure the directory exists
                ensure_dir(local_filename)
                # Save the image
                if save_image(image_url, session, local_filename):
                    # Update session progress
                    completed_urls.add(image_url)
                    save_session_state(session_number, {'completed_urls': list(completed_urls)})

        # Append the session info to the overall log
        session_info = [csv_file_path, session_number, len(completed_urls)]
        update_overall_log(OVERALL_LOG_PATH_TEMPLATE.format(session_number=session_number), session_info)

        # Move the renamed CSV to the completed folder
        os.rename(csv_file_path, COMPLETED_CSV_PATH_TEMPLATE.format(session_number=session_number))

# Main script execution
if __name__ == '__main__':
    # Get command-line arguments
    if len(sys.argv) < 3:
        print("Usage: python multidownload8.py <session_count> <session_number>")
        exit()

    session_count = int(sys.argv[1])
    session_number = int(sys.argv[2])

    # Check if the input is within the acceptable range
    if session_count < 1 or session_count > 40:
        raise ValueError("Session count must be between 1 and 40.")

    # Check for disk space before starting the download process
    try:
        check_disk_space(MIN_FREE_SPACE_MB)
    except Exception as e:
        print(e)
        exit()

    # Update the paths with the current session number
    csv_file_path = CSV_FILE_PATH_TEMPLATE.format(session_number=session_number)
    
    # Create a session
    session = requests.Session()
    
    # Main processing logic
    process_urls(csv_file_path, session_number, session)
    
    # Move the renamed CSV to the completed folder
    os.rename(csv_file_path, COMPLETED_CSV_PATH_TEMPLATE.format(session_number=session_number))

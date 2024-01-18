
import os
import time
import json
import pandas as pd
import requests
import csv
import re
from requests.exceptions import ConnectionError, Timeout, RequestException
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from datetime import datetime
import shutil
from urllib.parse import urlparse, unquote

# Constants
LOGIN_URL = "https://maticneknjige.org.rs/wp-login.php"
CHUNK_SIZE = 32768  # Chunk size set to 32 KB
MAX_FAILS = 1  # Maximum number of consecutive fails before skipping to next 'state'
MIN_FREE_SPACE_MB = 500  # Minimum free space required in MB to continue downloads
RETRY_DELAYS = [1, 2, 4, 8, 16, 32, 64]  # Exponential backoff retry delays in seconds
DOWNLOAD_PATH = "/path/to/download"  # Update this path to where you want to download images

# Paths
SESSION_DATA_PATH = "/home/pi/session_data"  # Path to save session data for persistence
OVERALL_LOG_PATH = "/home/pi/serbia/overall-log/overall-log.csv"  # Path to the overall log file

# Ensure session data and download directory exist
os.makedirs(SESSION_DATA_PATH, exist_ok=True)
os.makedirs(DOWNLOAD_PATH, exist_ok=True)

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
    if not check_disk_space(MIN_FREE_SPACE_MB):
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

# Main script execution
if __name__ == '__main__':
    # Ask user for input
    session_count = int(input("How many sessions to load (1-40): "))

    # Check if the input is within the acceptable range
    if session_count < 1 or session_count > 40:
        raise ValueError("Session count must be between 1 and 40.")

    # Check for disk space before starting the download process
    if not check_disk_space(MIN_FREE_SPACE_MB):
        print("Insufficient disk space to start the download.")
        exit()

    # Launch LXTerminal windows with tabs
    for i in range(1, session_count + 1):
        os.system(f"lxterminal --command='bash -c \"python3 {__file__} {i}; exec bash\"' &")
        time.sleep(0.5)  # Add a brief delay to prevent overwhelming the system

    # Ensure that the sessions are not closed immediately after the script ends
    input("Press Enter to close all sessions...")

# The function to process URLs and download images
def process_urls(csv_file_path, session_number, session):
    # Load session progress
    progress_data = load_session_state(session_number)
    completed_urls = progress_data.get('completed_urls', set())

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
            local_filename = os.path.join(DOWNLOAD_PATH, os.path.basename(image_url))
            # Ensure the directory exists
            ensure_dir(local_filename)
            # Save the image
            if save_image(image_url, session, local_filename):
                # Update session progress
                completed_urls.add(image_url)
                save_session_state(session_number, {'completed_urls': list(completed_urls)})

    # Append the session info to the overall log
    session_info = [csv_file_path, session_number, len(completed_urls)]
    update_overall_log(OVERALL_LOG_PATH, session_info)

# Ask the user to enter the session number
session_number = input("Enter session number (1 or greater): ")
# Initialize a new requests session
session = requests.Session()

try:
    # Placeholder for CSV file path, replace with your actual CSV file containing image URLs
    csv_file_path = "/path/to/your/csv_file.csv"
    # Main processing logic
    process_urls(csv_file_path, int(session_number), session)
except Exception as e:
    print(f"An error occurred: {e}")

# Close the browser after completing the downloads
browser.quit()

# Define a function to get image numbers from URL and determine the range and pattern
def get_image_range_and_pattern(df):
    image_numbers = []
    pattern_set = set()
    for image_url in df['URL']:
        # Extract image number from URL
        image_no = re.search(r'(\d+)\.jpg$', image_url)
        if image_no:
            image_numbers.append(int(image_no.group(1)))
            pattern_set.add(len(image_no.group(1)))
    if image_numbers:
        min_image_no = min(image_numbers)
        max_image_no = max(image_numbers)
        patterns = ''.join(sorted({f'{p}n' for p in pattern_set}, reverse=True))
    else:
        min_image_no, max_image_no, patterns = 0, 0, 'unknown'
    return min_image_no, max_image_no, patterns

# Define a function to check for late start in image sequence
def check_late_start(df):
    for image_url in df['URL']:
        image_no = re.search(r'(\d+)\.jpg$', image_url)
        if image_no and int(image_no.group(1)) > 1:
            return 'latestart___'
    return ''

# Define a function to check for gaps in image sequence
def check_gaps(df):
    image_numbers = sorted({int(re.search(r'(\d+)\.jpg$', url).group(1)) for url in df['URL'] if re.search(r'(\d+)\.jpg$', url)})
    if image_numbers and (max(image_numbers) - min(image_numbers) + 1 != len(image_numbers)):
        return 'gapsfound___'
    return ''
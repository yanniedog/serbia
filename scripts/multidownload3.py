import os
import time
import pandas as pd
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from urllib.parse import urlparse, unquote
from datetime import datetime, timedelta
import shutil

# Constants
USERNAME = "jkokavec@gmail.com"
PASSWORD = "Jwm^Z7Y%(kt"
LOGIN_URL = "https://maticneknjige.org.rs/wp-login.php"
CHUNK_SIZE = 32768  # Chunk size set to 32 KB
MAX_FAILS = 1  # Maximum number of consecutive fails before skipping to next 'state'
MIN_FREE_SPACE_MB = 500  # Minimum free space required in MB to continue downloads
RETRY_DELAYS = [1, 2, 4, 8, 16, 32, 64]  # Exponential backoff retry delays in seconds

# Paths
SESSION_DATA_PATH = "/home/pi/session_data"  # Path to save session data for persistence

# Ensure session data directory exists
os.makedirs(SESSION_DATA_PATH, exist_ok=True)

# Function to check if there is enough disk space to proceed
def check_disk_space(required_space_mb, path="/"):
    total, used, free = shutil.disk_usage(path)
    free_mb = free // (2**20)
    return free_mb >= required_space_mb

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
    return None

import json
from requests.exceptions import ConnectionError, Timeout, RequestException

# Function to ensure directory exists
def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

# Function to log image not found
def log_image_not_found(log_file_path, url):
    with open(log_file_path, 'a') as log_file:
        log_file.write(f"{datetime.now().strftime('%Y%m%d-%H:%M:%S')},{url}\n")

# Exponential backoff function
def backoff(retry_num):
    time.sleep(RETRY_DELAYS[min(retry_num, len(RETRY_DELAYS)-1)])

# Function to initialize Selenium browser in headless mode
def init_browser():
    options = Options()
    options.add_argument("--headless")
    service = Service('/usr/local/bin/geckodriver')
    return webdriver.Firefox(options=options, service=service)

# Start the browser session in headless mode
browser = init_browser()

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

# Section 3 of 6

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

# Define a function to get if there are duplicate image numbers in different URLs
def get_duplicates_status(df):
    seen = set()
    has_duplicates = False
    for image_url in df['URL']:
        image_no = re.search(r'(\d+)\.jpg$', image_url)
        if image_no and image_no.group(1) in seen:
            has_duplicates = True
            break
        seen.add(image_no.group(1))
    return 'dups' if has_duplicates else 'nodups'

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

# Define a function to check disk space
def check_disk_space(threshold=10):
    # Check disk space on device
    total, used, free = shutil.disk_usage("/")
    free_gb = free // (2**30)  # Convert from bytes to GB
    if free_gb < threshold:
        raise RuntimeError(f"Disk space is below the threshold. Only {free_gb} GB left.")

# Define exponential backoff strategy
def exponential_backoff(attempt, base_delay=0.5, max_delay=60):
    delay = min(base_delay * 2 ** attempt, max_delay)
    time.sleep(delay)

# Section 4 of 6

# Define a function for updating the overall log
def update_overall_log(log_path, session_info):
    with open(log_path, 'a', newline='', encoding='utf-8') as log_file:
        log_writer = csv.writer(log_file)
        log_writer.writerow(session_info)

# Main script execution
if __name__ == '__main__':
    # Ask user for input
    session_count = int(input("How many sessions to load (1-40): "))

    # Check if the input is within the acceptable range
    if session_count < 1 or session_count > 40:
        raise ValueError("Session count must be between 1 and 40.")

    # Check for disk space before starting the download process
    check_disk_space()

    # Launch LXTerminal windows with tabs
    for i in range(1, session_count + 1):
        session_num = (i - 1) % 10 + 1
        terminal_num = (i - 1) // 10 + 1

        if session_num == 1:  # First tab in a new terminal window
            os.system(f"lxterminal --command='bash -c \"python3 {script_name} {i}; exec bash\"' &")
        else:  # Subsequent tabs in the same terminal window
            os.system(f"lxterminal --tabs={','.join(map(str, range(1, session_num + 1)))} "
                      f"--command='bash -c \"python3 {script_name} {i}; exec bash\"' &")

        # Add a brief delay to prevent overwhelming the system with terminal openings
        time.sleep(0.5)

    # Ensure that the sessions are not closed immediately after the script ends
    input("Press Enter to close all sessions...")

    # Update the overall log with the session information
    update_overall_log("/home/pi/serbia/overall-log/overall-log.csv", session_info)

# Section 5 of 6

# Setup the browser for headless operation
options = Options()
options.headless = True
service = Service('/path/to/geckodriver')  # Update the path to geckodriver accordingly
browser = webdriver.Firefox(service=service, options=options)

# Add session persistence, exponential backoff, and disk space check features
# Function to load the session progress
def load_session_progress(session_file):
    if os.path.exists(session_file):
        with open(session_file, 'r') as file:
            return json.load(file)
    return {}

# Function to save the session progress
def save_session_progress(session_file, progress_data):
    with open(session_file, 'w') as file:
        json.dump(progress_data, file)

# Add exponential backoff to the existing check_image_with_session function
def check_image_with_session(url, session, retries=3):
    attempt = 0
    while attempt < retries:
        try:
            response = session.head(url, allow_redirects=True, timeout=10)
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException as e:
            print(f"Error for URL {url}: {e}")
            attempt += 1
            exponential_backoff(attempt)
    return False

# Add disk space check before saving the image
def save_image(url, session, file_path):
    check_disk_space()  # Check disk space before saving the image
    # ... rest of the save_image function ...

# Section 6 of 6

# Complete the main downloading and processing logic
# The function to process URLs and download images
def process_urls(csv_file_path, session_number, session_file):
    # Load session progress
    progress_data = load_session_progress(session_file)
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
            local_filename = os.path.join(download_path, os.path.basename(image_url))
            # Save the image
            save_image(image_url, session, local_filename)

        # Update session progress
        completed_urls.add(image_url)
        save_session_progress(session_file, {'completed_urls': list(completed_urls)})

    # Once all URLs are processed, rename the CSV to indicate it's done
    timestamp = datetime.now().strftime('%Y%m%d__%H%M%S')
    min_image_no, max_image_no, patterns = get_image_range_and_pattern(df)
    duplicates_status = get_duplicates_status(df)
    latestart_status = check_late_start(df)
    gaps_status = check_gaps(df)
    total_images = len(df)
    found_images = len([1 for url in df['URL'] if os.path.isfile(os.path.join(download_path, os.path.basename(url)))])
    saved_images = len([1 for url in df['URL'] if url in completed_urls])
    new_csv_file_path = f"{csv_file_path}___{timestamp}___range({min_image_no}-{max_image_no})___{patterns}___{duplicates_status}___{latestart_status}{gaps_status}t{total_images}e{found_images}s{saved_images}___sess{session_number}___d{download_duration}___r{restart_count}.done"
    os.rename(csv_file_path, new_csv_file_path)

    # Append the session info to the overall log
    session_info = [csv_file_path, timestamp, f"{min_image_no}-{max_image_no}", patterns, duplicates_status, latestart_status, gaps_status, total_images, found_images, saved_images, session_number, download_duration, restart_count]
    update_overall_log("/home/pi/serbia/overall-log/overall-log.csv", session_info)

# Ask the user to enter the session number
session_number = input("Enter session number (1 or greater): ")
# Initialize session_file based on the session_number
session_file = f"/path/to/session_progress_{session_number}.json"  # Update the path accordingly

try:
    # Main processing logic
    process_urls(csv_file_path, session_number, session_file)
except Exception as e:
    print(f"An error occurred: {e}")

# Close the browser after completing the downloads
browser.quit()


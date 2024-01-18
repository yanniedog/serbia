import os
import time
import pandas as pd
import requests
from urllib.parse import urlparse, unquote
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from datetime import datetime

# Prompt user for session number
session_number = input("Enter session number (1 or greater): ")
if not session_number:
    session_number = "1"
else:
    try:
        session_number = int(session_number)
        if session_number < 1:
            raise ValueError
        session_number = str(session_number)
    except ValueError:
        print("Invalid session number. Using session 1.")
        session_number = "1"

# Constants
USERNAME = "jkokavec@gmail.com"
PASSWORD = "Jwm^Z7Y%(kt"
LOGIN_URL = "https://maticneknjige.org.rs/wp-login.php"
CSV_DIRECTORY = f'/home/pi/serbia/excel/settlement_csvs{session_number}'
LOCAL_IMAGE_BASE_PATH = f'downloaded_images{session_number}'
MAX_FAILS = 1  # Maximum number of consecutive fails before skipping to next 'state'
LOG_FILE_PATH = f'/home/pi/serbia/logs{session_number}/images_not_found.csv'
COMPLETED_CSV_DIRECTORY = f'/home/pi/serbia/completed_csvs{session_number}'
CHUNK_SIZE = 32768  # Chunk size set to 32 KB

# Ensure the base directory for images and completed CSVs exists
os.makedirs(LOCAL_IMAGE_BASE_PATH, exist_ok=True)
os.makedirs(COMPLETED_CSV_DIRECTORY, exist_ok=True)
os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)

# Function to ensure directory exists
def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

# Function to log image not found
def log_image_not_found(url):
    with open(LOG_FILE_PATH, 'a') as log_file:
        log_file.write(f"{datetime.now().strftime('%Y%m%d-%H:%M:%S')},{url}\n")

# Start the browser session with explicit path to geckodriver
service = Service('/usr/local/bin/geckodriver')
browser = webdriver.Firefox(service=service)

# Function to check image existence with session
def check_image_with_session(url, session):
    response = session.head(url)
    return response.status_code == 200

# Function to download image with session
def download_image_with_session(image_url, local_image_path, session):
    try:
        response = session.get(image_url, stream=True)
        response.raise_for_status()
        ensure_dir(local_image_path)
        with open(local_image_path, 'wb') as out_file:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                out_file.write(chunk)
        return True
    except Exception as e:
        print(f"Failed to download {image_url}. Reason: {str(e)}")
        return False

session = requests.Session()

try:
    # Log in to the site
    browser.get(LOGIN_URL)
    username_field = browser.find_element(By.ID, "user_login")
    password_field = browser.find_element(By.ID, "user_pass")
    submit_button = browser.find_element(By.ID, "wp-submit")
    username_field.send_keys(USERNAME)
    password_field.send_keys(PASSWORD)
    submit_button.click()
    time.sleep(5)  # Wait for login to process

    # After login, extract cookies from Selenium and add to requests.Session
    selenium_cookies = browser.get_cookies()
    for cookie in selenium_cookies:
        session.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'])

    # Check if log file exists, if not, create with header
    if not os.path.exists(LOG_FILE_PATH):
        with open(LOG_FILE_PATH, 'w') as log_file:
            log_file.write("Date_Time,URL\n")

    # Process CSV files and download images
    csv_files = sorted([f for f in os.listdir(CSV_DIRECTORY) if f.endswith('.csv')])
    for csv_file in csv_files:
        print(f'Processing {csv_file}')
        df = pd.read_csv(os.path.join(CSV_DIRECTORY, csv_file))
        previous_state = None
        fail_count = 0
        image_not_found_count = 0

        for _, row in df.iterrows():
            image_url = row['URL']
            parsed_url = urlparse(image_url)
            url_parts = parsed_url.path.split('/')
            current_state = url_parts[-2]  # Assuming 'state' is the second to last element

            # Check if we should skip to the next state
            if previous_state and current_state != previous_state and fail_count >= MAX_FAILS:
                fail_count = 0  # Reset fail count on state change

            # Increment fail count or reset if state has changed
            if fail_count >= MAX_FAILS and current_state == previous_state:
                continue  # Skip to next URL within the loop

            local_image_path = os.path.join(LOCAL_IMAGE_BASE_PATH, unquote(parsed_url.path.lstrip('/')))

            if os.path.exists(local_image_path):
                print(f"Image already exists at {local_image_path}")
                continue

            if check_image_with_session(image_url, session):
                if download_image_with_session(image_url, local_image_path, session):
                    print(f"Downloaded image from {image_url} to {local_image_path}")
                    fail_count = 0  # Reset the fail count on a successful download
                else:
                    fail_count += 1
                    print(f'Failed to download image at {image_url}')
            else:
                fail_count += 1
                image_not_found_count += 1
                print(f'Image not found at {image_url}')
                log_image_not_found(image_url)

            previous_state = current_state  # Update previous state for next iteration

            time.sleep(0.1)

        # Rename and move completed CSV
        total_urls = len(df)
        missed_pct = (image_not_found_count / total_urls) * 100
        new_filename = f"done__missed_{image_not_found_count}_of_{total_urls}_({missed_pct:.2f}_pct)__{datetime.now().strftime('%Y%m%d_%H%M%S')}__{csv_file}"
        os.rename(os.path.join(CSV_DIRECTORY, csv_file), os.path.join(COMPLETED_CSV_DIRECTORY, new_filename))
        print(f"Completed {csv_file} and moved to {COMPLETED_CSV_DIRECTORY}")

finally:
    browser.quit()

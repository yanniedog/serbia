import os
import time
import pandas as pd
import requests
from urllib.parse import urlparse, unquote
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from datetime import datetime
import sys
import csv
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='(#{session_number}): %(asctime)s - %(levelname)s - %(message)s')

# Helper function to print messages with session number
def print_with_session_number(session_number, message):
    logging.debug(f"(#{session_number}): {message}")

# Function to ensure directory exists
def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

# Function to log image not found
def log_image_not_found(url, log_file_path):
    with open(log_file_path, 'a') as log_file:
        log_file.write(f"{datetime.now().strftime('%Y%m%d-%H:%M:%S')},{url}\n")

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
        print_with_session_number(session_number, f"Failed to download {image_url}. Reason: {str(e)}")
        return False

# Function to update the status column in the DataFrame and save the updated DataFrame to the CSV file
def update_status_and_save_csv(df, csv_path, index, status):
    if 'Status' not in df.columns:
        df['Status'] = pd.Series([''] * len(df))

    df.at[index, 'Status'] = status
    df.to_csv(csv_path, index=False)

# Function to update weights
def update_weights(df, index):
    for attr in ['religion', 'year', 'state']:
        weight_column = f"{attr}_weight"
        df.at[index, weight_column] += 1

# Function to get row weight
def get_row_weight(row):
    weight = 1
    for attr in ['religion', 'year', 'state']:
        weight *= row[f"{attr}_weight"]
    return weight

# Main function to process CSVs and download images
def process_images(session_number, session, browser):
    CSV_DIRECTORY = f'/home/pi/serbia/excel/settlement_csvs{session_number}'
    LOCAL_IMAGE_BASE_PATH = f'downloaded_images{session_number}'
    LOG_FILE_PATH = f'/home/pi/serbia/logs{session_number}/images_not_found.csv'
    os.makedirs(LOCAL_IMAGE_BASE_PATH, exist_ok=True)
    os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)

    if not os.path.exists(LOG_FILE_PATH):
        with open(LOG_FILE_PATH, 'w') as log_file:
            log_file.write("Date_Time,URL\n")

    csv_files = sorted([f for f in os.listdir(CSV_DIRECTORY) if f.endswith('.csv')])
    start_time = time.time()

    for csv_file in csv_files:
        try:
            print_with_session_number(session_number, f'Processing {csv_file}')
            csv_path = os.path.join(CSV_DIRECTORY, csv_file)
            df = pd.read_csv(csv_path)
            if df.empty:
                raise ZeroDivisionError("CSV is empty, indicating an upstream issue.")

            for attr in ['religion', 'year', 'state']:
                weight_column = f"{attr}_weight"
                if weight_column not in df.columns:
                    df[weight_column] = 1

            if 'Status' not in df.columns:
                df['Status'] = ''

            while (df['Status'] == '').any():
                df['Weight'] = df.apply(get_row_weight, axis=1)
                selected_row = df[df['Status'] == ''].sample(weights='Weight').iloc[0]
                selected_index = df[df['URL'] == selected_row['URL']].index[0]

                image_url = selected_row['URL']
                local_image_path = os.path.join(LOCAL_IMAGE_BASE_PATH, unquote(urlparse(image_url).path.lstrip('/')))

                # Check if image already exists
                if not os.path.exists(local_image_path):
                    if check_image_with_session(image_url, session):
                        print_with_session_number(session_number, f"Downloading image: {image_url}")
                        if download_image_with_session(image_url, local_image_path, session):
                            update_status_and_save_csv(df, csv_path, selected_index, 'Downloaded')
                        else:
                            log_image_not_found(image_url, LOG_FILE_PATH)
                            update_status_and_save_csv(df, csv_path, selected_index, 'Failed')
                    else:
                        print_with_session_number(session_number, f"Image not found: {image_url}")
                        log_image_not_found(image_url, LOG_FILE_PATH)
                        update_status_and_save_csv(df, csv_path, selected_index, 'Not Found')
                else:
                    print_with_session_number(session_number, f"Image already exists: {local_image_path}")
                    update_status_and_save_csv(df, csv_path, selected_index, 'Exists')

                # Update weights
                update_weights(df, selected_index)
        except Exception as e:
            print_with_session_number(session_number, f"An error occurred while processing {csv_file}: {str(e)}")

    elapsed_time = time.time() - start_time
    print_with_session_number(session_number, f"Completed processing CSV files in {elapsed_time:.2f} seconds")

# Constants and configurations
CHUNK_SIZE = 1024 * 1024  # 1MB chunk size for image download
LOG_FILE_PATH = '/home/pi/logs/images_not_found.csv'
IMAGE_DIRECTORY = '/home/pi/images'
CSV_DIRECTORY = '/home/pi/csvs'

# Ensure directories exist
os.makedirs(IMAGE_DIRECTORY, exist_ok=True)
os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)

# Initialize log file if it does not exist
if not os.path.exists(LOG_FILE_PATH):
    with open(LOG_FILE_PATH, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "URL"])

# Main script starts here
if __name__ == "__main__":
    session_number = int(sys.argv[1]) if len(sys.argv) > 1 else 1

    # Set up session and browser
    session = requests.Session()
    browser = start_browser()

    # Log in to the website
    browser.get(LOGIN_URL)
    username_field = browser.find_element(By.ID, "user_login")
    password_field = browser.find_element(By.ID, "user_pass")
    submit_button = browser.find_element(By.ID, "wp-submit")

    username_field.send_keys(USERNAME)
    password_field.send_keys(PASSWORD)
    submit_button.click()

    # Wait for login to process
    time.sleep(5)

    # Transfer cookies to session
    selenium_cookies = browser.get_cookies()
    for cookie in selenium_cookies:
        session.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'])

    # Close browser after login
    browser.quit()

    # Start processing CSV files
    process_images(session_number, session)

def process_images(session_number, session):
    csv_files = sorted([f for f in os.listdir(CSV_DIRECTORY) if f.endswith('.csv')])

    for csv_file in csv_files:
        csv_path = os.path.join(CSV_DIRECTORY, csv_file)
        df = pd.read_csv(csv_path)

        if df.empty:
            print(f"(Session {session_number}): CSV '{csv_file}' is empty.")
            continue

        print(f"(Session {session_number}): Processing CSV '{csv_file}'.")

        for index, row in df.iterrows():
            image_url = row['URL']
            local_image_path = get_local_image_path(image_url)

            if os.path.exists(local_image_path):
                print(f"(Session {session_number}): Image already exists at '{local_image_path}'.")
                continue

            if check_image(image_url, session):
                download_image(image_url, local_image_path, session)
            else:
                log_image_not_found(image_url)

        print(f"(Session {session_number}): Finished processing CSV '{csv_file}'.")

# Constants and configurations
CSV_DIRECTORY = '/home/pi/serbia/csvs'
IMAGE_DIRECTORY = '/home/pi/serbia/images'
LOG_FILE_PATH = '/home/pi/serbia/logs/images_not_found.log'
CHUNK_SIZE = 2048  # How much data to download at once.

# Ensure base directories exist
ensure_directory_exists(CSV_DIRECTORY)
ensure_directory_exists(IMAGE_DIRECTORY)
ensure_directory_exists(os.path.dirname(LOG_FILE_PATH))

# Main execution
if __name__ == "__main__":
    session_number = 1  # Set the session number here.

    # Start session
    session = requests.Session()

    # Begin processing images
    process_images(session_number, session)

    print(f"(Session {session_number}): Script execution finished.")


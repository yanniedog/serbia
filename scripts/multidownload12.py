import os
import time
import pandas as pd
import requests
import json
from urllib.parse import urlparse, unquote
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from datetime import datetime
import sys
import csv

# Helper function to print messages with session number
def print_with_session_number(session_number, message):
    print(f"(#{session_number}): {message}")

# Function to initialize the overall log file
def init_overall_log(log_file_path):
    if not os.path.exists(log_file_path):
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
        with open(log_file_path, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                "Original Filename", "Completion Timestamp", "Image Range", "Digit Format",
                "Duplication Status", "Late Start", "Gaps Found", "Total Listed Images",
                "Images Found Locally", "Images Saved", "Session Number",
                "Execution Duration", "Restart Count"
            ])
    print_with_session_number(session_number, f"Initialized overall log file at {log_file_path}")

# Function to ensure directory exists
def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

# Function to log image not found
def log_image_not_found(url, log_file_path):
    with open(log_file_path, 'a') as log_file:
        log_file.write(f"{datetime.now().strftime('%Y%m%d-%H:%M:%S')},{url}\n")

# Function to write to overall log
def write_to_overall_log(log_file_path, data):
    with open(log_file_path, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(data)

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

# Function to rename and log completed CSV
def rename_completed_csv(original_csv_path, completed_csv_directory, stats, session_number, restart_count, duration):
    filename = os.path.basename(original_csv_path)
    prefix = f"___{datetime.now().strftime('%Y%m%d__%H%M%S')}___range({stats['smallest_image']}-{stats['largest_image']})___{stats['digit_format']}___{stats['dup_status']}___"
    if stats['late_start']:
        prefix += "latestart___"
    if stats['gaps_found']:
        prefix += "gapsfound___"
    prefix += f"t{stats['total_images']}e{stats['existing_images']}s{stats['saved_images']}___sess{session_number}___d{duration}___r{restart_count}"
    new_filename = f"{filename}{prefix}.done"
    os.rename(original_csv_path, os.path.join(completed_csv_directory, new_filename))
    return new_filename

# Function to parse image numbers and track stats
def parse_image_numbers(df):
    stats = {
        'smallest_image': float('inf'),
        'largest_image': 0,
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
        stats['smallest_image'] = min(stats['smallest_image'], image_number)
        stats['largest_image'] = max(stats['largest_image'], image_number)
    
    if all(len(str(num)) == 3 for num in seen_numbers):
        stats['digit_format'] = '3n'
    elif all(len(str(num)) == 4 for num in seen_numbers):
        stats['digit_format'] = '4n'
    else:
        stats['digit_format'] = '3-4n'
    
    stats['dup_status'] = 'dups' if len(seen_numbers) < stats['total_images'] else 'nodups'
    stats['late_start'] = not (1 in seen_numbers or '0001' in seen_numbers or '001' in seen_numbers)
    stats['gaps_found'] = not all(num in seen_numbers for num in range(stats['smallest_image'], stats['largest_image'] + 1))
    
    return stats

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
    COMPLETED_CSV_DIRECTORY = f'/home/pi/serbia/completed_csvs{session_number}'
    os.makedirs(LOCAL_IMAGE_BASE_PATH, exist_ok=True)
    os.makedirs(COMPLETED_CSV_DIRECTORY, exist_ok=True)
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

            stats = parse_image_numbers(df)

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

                if os.path.exists(local_image_path):
                    stats['existing_images'] += 1
                    print_with_session_number(session_number, f"Image already exists at {local_image_path}")
                    update_status_and_save_csv(df, csv_path, selected_index, 'E')
                elif check_image_with_session(image_url, session):
                    if download_image_with_session(image_url, local_image_path, session):
                        stats['saved_images'] += 1
                        print_with_session_number(session_number, f"Downloaded image from {image_url} to {local_image_path}")
                        update_status_and_save_csv(df, csv_path, selected_index, 'D')
                        update_weights(df, selected_index)
                    else:
                        print_with_session_number(session_number, f'Failed to download image at {image_url}')
                else:
                    print_with_session_number(session_number, f'Image not found at {image_url}')
                    log_image_not_found(image_url, LOG_FILE_PATH)
                    update_status_and_save_csv(df, csv_path, selected_index, 'N')

            duration = int(time.time() - start_time)
            new_filename = rename_completed_csv(
                csv_path, COMPLETED_CSV_DIRECTORY, stats, session_number, restart_count, duration
            )

            write_to_overall_log(OVERALL_LOG_PATH, [
                csv_file, datetime.now().strftime('%Y%m%d__%H%M%S'),
                f"{stats['smallest_image']}-{stats['largest_image']}", stats['digit_format'],
                stats['dup_status'], 'latestart' if stats['late_start'] else '',
                'gapsfound' if stats['gaps_found'] else '', stats['total_images'],
                stats['existing_images'], stats['saved_images'], session_number,
                duration, restart_count
            ])

            print_with_session_number(session_number, f"Completed {csv_file} and moved to {COMPLETED_CSV_DIRECTORY}")

        except KeyboardInterrupt:
            print_with_session_number(session_number, "Terminating the script due to KeyboardInterrupt.")
            return False, restart_count
        except Exception as e:
            if restart_count < MAX_RESTARTS:
                print_with_session_number(session_number, f"An error occurred: {e}. Restarting processing for CSV: {csv_file}")
                restart_count += 1
                time.sleep(10)
                process_images(session_number, session, browser)
            else:
                print_with_session_number(session_number, f"Reached maximum restarts ({MAX_RESTARTS}). Terminating the script.")
                return False, restart_count
        else:
            print_with_session_number(session_number, "Processing completed without any errors.")
            return True, restart_count

# Constants
USERNAME = "jkokavec@gmail.com"
PASSWORD = "Jwm^Z7Y%(kt"
LOGIN_URL = "https://maticneknjige.org.rs/wp-login.php"
CHUNK_SIZE = 32768  # Chunk size set to 32 KB
OVERALL_LOG_PATH = '/home/pi/serbia/overall-log/overall-log.csv'
MAX_RESTARTS = 100

def start_browser():
    service = Service('/usr/local/bin/geckodriver')
    options = Options()
    options.add_argument('-headless')
    browser = webdriver.Firefox(service=service, options=options)
    return browser

if __name__ == "__main__":
    session_number = int(sys.argv[1])

    init_overall_log(OVERALL_LOG_PATH)

    print_with_session_number(session_number, "Starting main script execution")

    if len(sys.argv) < 3:
        print_with_session_number(session_number, "Usage: python multidownload9.py <session_count> <session_number>")
        sys.exit(1)

    session = requests.Session()

    browser = None
    completed_successfully = False
    try:
        browser = start_browser()

        browser.get(LOGIN_URL)
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

        completed_successfully, restart_count = process_images(session_number, session, browser)

    except KeyboardInterrupt:
        completed_successfully = False
    finally:
        if browser:
            browser.quit()
        if not completed_successfully:
            sys.exit(1)

    print_with_session_number(session_number, "Finished main script execution")

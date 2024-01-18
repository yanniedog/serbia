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
        print(f"Failed to download {image_url}. Reason: {str(e)}")
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
        # Update stats
        stats['smallest_image'] = min(stats['smallest_image'], image_number)
        stats['largest_image'] = max(stats['largest_image'], image_number)
    
    # Determine digit format
    if all(len(str(num)) == 3 for num in seen_numbers):
        stats['digit_format'] = '3n'
    elif all(len(str(num)) == 4 for num in seen_numbers):
        stats['digit_format'] = '4n'
    else:
        stats['digit_format'] = '3-4n'
    
    # Check for duplicates and gaps
    stats['dup_status'] = 'dups' if len(seen_numbers) < stats['total_images'] else 'nodups'
    stats['late_start'] = not (1 in seen_numbers or '0001' in seen_numbers or '001' in seen_numbers)
    stats['gaps_found'] = not all(num in seen_numbers for num in range(stats['smallest_image'], stats['largest_image'] + 1))
    
    return stats

# Constants
USERNAME = "jkokavec@gmail.com"
PASSWORD = "Jwm^Z7Y%(kt"
LOGIN_URL = "https://maticneknjige.org.rs/wp-login.php"
CHUNK_SIZE = 32768  # Chunk size set to 32 KB
OVERALL_LOG_PATH = '/home/pi/serbia/overall-log/overall-log.csv'

# Initialize overall log file
init_overall_log(OVERALL_LOG_PATH)

# Start the browser session with explicit path to geckodriver and headless option
service = Service('/usr/local/bin/geckodriver')
options = Options()
options.headless = True
browser = webdriver.Firefox(service=service, options=options)

# Main function to process CSVs and download images
def process_images(session_number, session, browser):
    CSV_DIRECTORY = f'/home/pi/serbia/excel/settlement_csvs{session_number}'
    LOCAL_IMAGE_BASE_PATH = f'downloaded_images{session_number}'
    LOG_FILE_PATH = f'/home/pi/serbia/logs{session_number}/images_not_found.csv'
    COMPLETED_CSV_DIRECTORY = f'/home/pi/serbia/completed_csvs{session_number}'
    os.makedirs(LOCAL_IMAGE_BASE_PATH, exist_ok=True)
    os.makedirs(COMPLETED_CSV_DIRECTORY, exist_ok=True)
    os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)

    # Check if log file exists, if not, create with header
    if not os.path.exists(LOG_FILE_PATH):
        with open(LOG_FILE_PATH, 'w') as log_file:
            log_file.write("Date_Time,URL\n")

    # Process CSV files and download images
    csv_files = sorted([f for f in os.listdir(CSV_DIRECTORY) if f.endswith('.csv')])
    start_time = time.time()
    restart_count = 0

    for csv_file in csv_files:
        try:
            print(f'Processing {csv_file}')
            df = pd.read_csv(os.path.join(CSV_DIRECTORY, csv_file))
            if df.empty:
                raise ZeroDivisionError("CSV is empty, indicating an upstream issue.")

            stats = parse_image_numbers(df)

            for _, row in df.iterrows():
                image_url = row['URL']
                local_image_path = os.path.join(LOCAL_IMAGE_BASE_PATH, unquote(urlparse(image_url).path.lstrip('/')))
                
                if os.path.exists(local_image_path):
                    stats['existing_images'] += 1
                    print(f"Image already exists at {local_image_path}")
                    continue
                
                if check_image_with_session(image_url, session):
                    if download_image_with_session(image_url, local_image_path, session):
                        stats['saved_images'] += 1
                        print(f"Downloaded image from {image_url} to {local_image_path}")
                    else:
                        print(f'Failed to download image at {image_url}')
                else:
                    print(f'Image not found at {image_url}')
                    log_image_not_found(image_url, LOG_FILE_PATH)

            # Rename and move completed CSV
            duration = int(time.time() - start_time)
            new_filename = rename_completed_csv(
                os.path.join(CSV_DIRECTORY, csv_file), COMPLETED_CSV_DIRECTORY, stats, session_number, restart_count, duration
            )
            
            # Log to overall log
            write_to_overall_log(OVERALL_LOG_PATH, [
                csv_file, datetime.now().strftime('%Y%m%d__%H%M%S'),
                f"{stats['smallest_image']}-{stats['largest_image']}", stats['digit_format'],
                stats['dup_status'], 'latestart' if stats['late_start'] else '',
                'gapsfound' if stats['gaps_found'] else '', stats['total_images'],
                stats['existing_images'], stats['saved_images'], session_number,
                duration, restart_count
            ])
            
            print(f"Completed {csv_file} and moved to {COMPLETED_CSV_DIRECTORY}")

        except Exception as e:
            print(f"An error occurred: {e}. Restarting processing for CSV: {csv_file}")
            restart_count += 1
            time.sleep(10)  # Wait before restarting to avoid rapid loops
            process_images(session_number, session, browser)  # Recursive call to retry processing

    return restart_count

# Main execution block
if __name__ == "__main__":
    print("Starting main script execution")

    # Prompt user for session number
    session_number = input("Enter session number (1 or greater): ")
    if not session_number or not session_number.isdigit() or int(session_number) < 1:
        session_number = "1"

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

        # Begin processing images
        restart_count = process_images(session_number, session, browser)

    except Exception as e:
        # In case of any error which is not specifically handled, write the error to the overall log
        with open(OVERALL_LOG_PATH, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([session_number, 'ERROR', 'ERROR', 'ERROR', 'ERROR', 'ERROR', 'ERROR', 'ERROR', 'ERROR', 'ERROR', 'ERROR', 'ERROR', str(e)])
        print(f"Unexpected error: {e}, terminating the script.")
        sys.exit(1)  # Terminate the script

    finally:
        browser.quit()

    print("Finished main script execution")

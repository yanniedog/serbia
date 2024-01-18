from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
import time
import os
import pandas as pd
import requests
from urllib.parse import urlparse, unquote

# Constants
USERNAME = "jkokavec@gmail.com"
PASSWORD = "Jwm^Z7Y%(kt"
LOGIN_URL = "https://maticneknjige.org.rs/wp-login.php"
CSV_DIRECTORY = 'settlement_csvs'
LOCAL_IMAGE_BASE_PATH = 'downloaded_images'

# Ensure the base directory for images exists
os.makedirs(LOCAL_IMAGE_BASE_PATH, exist_ok=True)

# Function to ensure directory exists
def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

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
            for chunk in response.iter_content(chunk_size=8192):
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

    # Process CSV files and download images
    for csv_file in os.listdir(CSV_DIRECTORY):
        if csv_file.endswith('.csv'):
            print(f'Processing {csv_file}')
            df = pd.read_csv(os.path.join(CSV_DIRECTORY, csv_file))

            for _, row in df.iterrows():
                image_url = row['URL']
                parsed_url = urlparse(image_url)
                local_image_path = os.path.join(LOCAL_IMAGE_BASE_PATH, unquote(parsed_url.path.lstrip('/')))

                if check_image_with_session(image_url, session):
                    if download_image_with_session(image_url, local_image_path, session):
                        print(f"Downloaded image from {image_url} to {local_image_path}")
                else:
                    print(f'Image not found at {image_url}')
                time.sleep(0.1)

finally:
    browser.quit()

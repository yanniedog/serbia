from serbia_scripts.config import (
    USERNAME,
    PASSWORD,
    CSV_DIRECTORY_BASE,
    LOCAL_IMAGE_BASE_PATH_BASE,
    LOG_FILE_PATH_BASE,
    COMPLETED_CSV_DIRECTORY_BASE,
    OVERALL_LOG_PATH,
    GECKODRIVER_PATH,
    BROWSER_OPTIONS,
    CHUNK_SIZE,
    MAX_RESTARTS,
    LOGIN_URL,
    SELENIUM_TIMEOUT,
)
from serbia_scripts.utils import (
    print_with_session_number,
    print_exception,
    ensure_dir,
)
from serbia_scripts.image_processing import (
    handle_image,
    parse_image_numbers,
    update_status_and_save_csv,
)
from serbia_scripts.browser import start_browser
from serbia_scripts.csv_processing import (
    process_images,
    init_overall_log,
    write_to_overall_log,
    rename_completed_csv,
)

from colorama import init
import sys
import os
import requests
import time
from datetime import datetime

# Initialize colorama
init(autoreset=True)

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

import pandas as pd
import csv
from datetime import datetime
from serbia_scripts.image_processing import handle_image, parse_image_numbers, update_status_and_save_csv
from serbia_scripts.utils import print_with_session_number, print_exception, ensure_dir

def process_images(csv_path, session, session_number, CHUNK_SIZE, LOG_FILE_PATH, LOCAL_IMAGE_BASE_PATH):
    all_status_assigned = True
    try:
        df = pd.read_csv(csv_path)
        if 'Status' not in df.columns:
            df['Status'] = None
        for attr in ['religion', 'year', 'state']:
            weight_column = f"{attr}_weight"
            if weight_column not in df.columns:
                df[weight_column] = 1
        if 'Weight' not in df.columns:
            df['Weight'] = df.apply(get_row_weight, axis=1)

        while df['Status'].isna().sum() > 0:
            unprocessed_df = df[df['Status'].isna()]
            selected_row = unprocessed_df.sample(weights='Weight').iloc[0]
            selected_index = selected_row.name

            image_url = selected_row['URL']
            local_image_path = os.path.join(LOCAL_IMAGE_BASE_PATH, *unquote(urlparse(image_url).path).split('/')[1:])

            if os.path.exists(local_image_path):
                print_with_session_number(session_number, f"Image already exists: {local_image_path}")
                df.at[selected_index, 'Status'] = 'E'
            else:
                if handle_image(image_url, local_image_path, session, session_number, CHUNK_SIZE):
                    df.at[selected_index, 'Status'] = 'D'
                else:
                    df.at[selected_index, 'Status'] = 'N'
                    log_image_not_found(image_url, LOG_FILE_PATH, session_number)

            df = update_weights(df, selected_index)
            df.to_csv(csv_path, index=False)

        all_status_assigned = df['Status'].isna().sum() == 0

    except pd.errors.EmptyDataError:
        print_with_session_number(session_number, "CSV is empty or corrupted.")
    except Exception as e:
        print_exception(session_number, e)

    stats = parse_image_numbers(df, session_number)
    return stats, all_status_assigned

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

def write_to_overall_log(log_file_path, data, session_number):
    with open(log_file_path, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(data)
    print_with_session_number(session_number, f"Wrote overall log entry: {data}")

def rename_completed_csv(original_csv_path, completed_csv_directory, stats, session_number, restart_count, duration):
    filename, ext = os.path.splitext(os.path.basename(original_csv_path))
    new_filename = f"{filename}_{session_number}_done.csv"
    os.rename(original_csv_path, os.path.join(completed_csv_directory, new_filename))
    print_with_session_number(session_number, f"Renamed CSV: {original_csv_path} to {new_filename}")
    return new_filename

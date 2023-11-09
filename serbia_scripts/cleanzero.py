import os
import csv
from datetime import datetime

def clear_screen():
    # Clear the console screen
    os.system('cls' if os.name == 'nt' else 'clear')

def manage_empty_files(base_directory):
    log_directory = "%(base)s/logs/cleanup-log"
    exclusion_file_path = os.path.join(log_directory, "exclusions.txt")
    log_file = os.path.join(log_directory, "cleanup-log.csv")
    
    if not os.path.exists(log_directory):
        os.makedirs(log_directory, exist_ok=True)
    
    if not os.path.exists(log_file):
        with open(log_file, 'w', newline='') as csvfile:
            log_writer = csv.writer(csvfile)
            log_writer.writerow(['Path', 'Filesize', 'Modification Time', 'Deletion Time', 'Backup Time', 'Backup Folder'])

    previous_exclusions = set()
    if os.path.exists(exclusion_file_path):
        with open(exclusion_file_path, 'r') as f:
            previous_exclusions = set(f.read().strip().split(','))

    if previous_exclusions:
        if input("Load the exclusion list from last time? (%(use_latest_script)s/no): ").strip().lower() == '%(use_latest_script)s':
            print("Exclusions loaded.")

    def find_empty_files(base_dir, exclusions):
        for root, dirs, files in os.walk(base_dir):
            for file in files:
                if file == "exclusions.txt" or file.endswith('.bak'):
                    continue
                file_path = os.path.join(root, file)
                if os.path.getsize(file_path) == 0 and file_path not in exclusions:
                    mod_time = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
                    yield (file_path, 0, mod_time)

    def get_backup_path(original_path, backup_folder):
        base_name = os.path.basename(original_path)
        backup_base_path = os.path.join(backup_folder, base_name)
        backup_path = backup_base_path + '.bak'
        counter = 1
        while os.path.exists(backup_path):
            backup_path = f"{backup_base_path}_{counter}.bak"
            counter += 1
        return backup_path

    empty_files = list(find_empty_files(base_directory, previous_exclusions))
    files_to_process = empty_files

    clear_screen()
    while files_to_process:
        print("Files to be processed:")
        for idx, file_info in enumerate(files_to_process, 1):
            print(f"{idx}. File: {file_info[0]}, Size: {file_info[1]}, Last Modified: {file_info[2]}")

        exclusions_input = input("Enter the numbers of files or directory paths you wish to exclude (comma-separated), or press Enter to proceed: ")
        if exclusions_input.strip():
            exclude_paths = set(exclusions_input.split(",")).union(previous_exclusions)
            exclude_dirs = {path.strip() for path in exclude_paths if os.path.isdir(path.strip())}
            exclude_file_indices = {int(e.strip()) for e in exclude_paths if e.strip().isdigit()}
            files_to_process = [file for file in files_to_process if not any(file[0].startswith(ex_dir) for ex_dir in exclude_dirs)]
            files_to_process = [file for i, file in enumerate(files_to_process, 1) if i not in exclude_file_indices]
            previous_exclusions.update(exclude_paths)
            with open(exclusion_file_path, 'w') as f:
                f.write(','.join(previous_exclusions))
        else:
            break
        clear_screen()

    if not files_to_process:
        print("No files left to process after exclusions. Exiting.")
        return

    response = input("Enter 'delete' to delete, 'backup' to move to backup folder, or 'exit'/'cancel'/'abort' to stop: ").strip().lower()
    if response not in {'delete', 'backup', 'exit', 'cancel', 'abort'} or response in {'exit', 'cancel', 'abort', ''}:
        print("Operation canceled. Exiting.")
        return

    backup_folder = "%(base)s/backup"
    if response == 'backup':
        custom_backup_folder = input("Enter a different backup folder path to use, or press Enter to use default: ").strip()
        if custom_backup_folder:
            backup_folder = custom_backup_folder
            if not os.path.exists(backup_folder):
                os.makedirs(backup_folder, exist_ok=True)

    activities = []
    for file_path, filesize, mod_time in files_to_process:
        if response == 'delete':
            os.remove(file_path)
            deletion_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            activities.append(f"Deleted: {file_path}")
        elif response == 'backup':
            backup_path = get_backup_path(file_path, backup_folder)
            os.rename(file_path, backup_path)
            backup_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            activities.append(f"Backed up: {file_path} to {backup_path}")
        
        with open(log_file, 'a', newline='') as csvfile:
            log_writer = csv.writer(csvfile)
            log_writer.writerow([file_path, filesize, mod_time, deletion_time, backup_time, backup_folder])

    for activity in activities:
        print(activity)

    print("Operation completed.")

base_directory = "%(base)s"
manage_empty_files(base_directory)

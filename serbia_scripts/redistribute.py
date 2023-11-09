import configparser
config = configparser.ConfigParser()
config.read(r'/home/pi/serbia/config/serbia.cfg')
import os
import re
import configparser
from datetime import datetime

# Function to format file information
def format_file_info(path):
    stat = os.stat(path)
    created = datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
    modified = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
    filesize = stat.st_size
    return f"{path} (Size: {filesize} bytes, Created: {created}, Modified: {modified})"

# Function to handle renaming with checks
def handle_renaming(original, new):
    if os.path.exists(new):
        print("Potential overwrite detected:")
        print("Source:", format_file_info(original))
        print("Destination:", format_file_info(new))
        response = input("Choose action: keep both (b), keep source (s), keep destination (d), abort (a) [default: abort]: ").strip().lower()
        # Keep both files, rename the source
        if response == 'b':
            base, extension = os.path.splitext(new)
            count = 1
            while os.path.exists(new):
                new = f"{base}_{count}{extension}"
                count += 1
            os.rename(original, new)
            print(f"Kept both: {original} has been renamed to {new}")
        # Keep the source, remove the destination
        elif response == 's':
            os.remove(new)
            os.rename(original, new)
            print(f"Kept source: {original} has been renamed to {new} and destination has been removed.")
        # Keep the destination, do nothing with the source
        elif response == 'd':
            print(f"Kept destination: No changes made for {original}.")
        # Abort the operation for this file
        else:
            print(f"Aborted: No changes made for {original}.")
    else:
        os.rename(original, new)
        print(f"Renamed: {original} to {new}")

# Load the configuration file
config = configparser.ConfigParser()
config.read('/home/pi/serbia/config/serbia.cfg')  # Update with the correct path to your serbia.cfg file

# Assign the base directory from the configuration file
csv_directory_base = config['DEFAULT']['csv_in']  # e.g., /home/pi/serbia/settlement_csvs/

# Compile a regular expression pattern to match files that need renaming
pattern = re.compile(r'^(.*?)(___.*?)(\.csv)$')

# List for storing proposed changes
proposed_changes = []

# Walk through the directory structure
for dirpath, dirnames, files in os.walk(csv_directory_base):
    for name in files:
        # Check if the file matches the pattern
        match = pattern.match(name)
        if match:
            original_path = os.path.join(dirpath, name)
            new_name = f"{match.group(1)}{match.group(3)}"
            new_path = os.path.join(dirpath, new_name)
            proposed_changes.append((original_path, new_path))

# Print proposed changes and ask for confirmation
for original, new in proposed_changes:
    print(f"Proposed change: {original} -> {new}")
response = input("Do you want to proceed with the proposed changes? (y/n): ").strip().lower()
if response == 'y':
    for original, new in proposed_changes:
        handle_renaming(original, new)
else:
    print("No changes have been made.")

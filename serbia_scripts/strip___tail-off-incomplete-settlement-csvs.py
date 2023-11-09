# This file is located at: /home/pi/serbia/scripts/strip-___-tail-off-incomplete-settlement-csvs.py

import os
import re
import configparser
from datetime import datetime

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
            # Get file stats
            stat = os.stat(original_path)
            created = datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
            modified = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            filesize = stat.st_size
            # Add the proposed change to the list
            proposed_changes.append((original_path, new_path, created, modified, filesize))

# Print proposed changes
for change in proposed_changes:
    print(f"File: {change[0]}")
    print(f" -> Rename to: {change[1]}")
    print(f" -> Created: {change[2]}, Modified: {change[3]}, Size: {change[4]} bytes")

# Ask user to confirm
response = input("Are you happy to proceed with these changes? (y/n): ").strip().lower()
if response == 'y':
    for original, new, _, _, _ in proposed_changes:
        os.rename(original, new)
    print("Files have been renamed.")
else:
    print("No changes have been made.")

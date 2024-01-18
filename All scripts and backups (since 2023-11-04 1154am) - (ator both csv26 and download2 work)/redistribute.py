
import os
import shutil
from pathlib import Path
from itertools import cycle

# Define the base directories
source_dirs = [f"settlement_csvs{i}" for i in range(1, 256)]
target_dir = "settlement_csvs"

# Ensure the target directory exists
Path(target_dir).mkdir(parents=True, exist_ok=True)

# Move all CSV files from each source directory to the target directory, checking for duplicates
for dir_path in source_dirs:
    path = Path(dir_path)
    if path.exists():
        for file in path.glob("*.csv"):
            target_file_path = Path(target_dir) / file.name
            if target_file_path.exists():
                # If the file already exists, we'll skip it or handle it according to your needs
                print(f"File {file.name} already exists in {target_dir}, skipping...")
                continue
            shutil.move(str(file), target_dir)

# List of all CSV files in the target directory
csv_files = list(Path(target_dir).glob("*.csv"))

# Distribute files back to source directories evenly, using cycle to iterate over directories
dir_cycle = cycle(source_dirs)
for file_path in csv_files:
    next_dir = Path(next(dir_cycle))
    # Ensure the directory exists
    next_dir.mkdir(parents=True, exist_ok=True)
    # Move the file to the next directory in the cycle, handling potential overwrites
    destination_file_path = next_dir / file_path.name
    if destination_file_path.exists():
        # If the file already exists in the destination, we'll rename the existing file
        existing_file_renamed = destination_file_path.with_suffix('.old.csv')
        os.rename(destination_file_path, existing_file_renamed)
    shutil.move(str(file_path), str(next_dir))

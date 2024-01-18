import os

# Define the base directory where the 'state' directories are located
base_dir = '/home/pi/serbia'  # The path provided by the user

# Function to list and confirm deletion of JSON files
def list_and_confirm_deletion(base_dir):
    # Generate directory names from state1 to state255
    state_dirs = [f"state{i}" for i in range(1, 256)]
    json_files = []

    # Iterate over each directory and list .json files
    for state_dir in state_dirs:
        dir_path = os.path.join(base_dir, state_dir)
        if os.path.exists(dir_path):
            for file in os.listdir(dir_path):
                if file.endswith(".json"):
                    json_files.append(os.path.join(dir_path, file))

    # List all .json files
    for file_path in json_files:
        print(file_path)

    # Ask for confirmation before deletion
    confirm = input("Do you want to delete all listed JSON files? (yes/no) ")

    # Perform deletion if confirmed
    if confirm.lower() == 'yes':
        for file_path in json_files:
            os.remove(file_path)
            print(f"Deleted JSON file: {file_path}")
    else:
        print("Deletion cancelled.")

# Call the function to list and confirm deletion of JSON files
list_and_confirm_deletion(base_dir)

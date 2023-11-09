import os
import time
import configparser

# Read configuration file
config = configparser.ConfigParser()
config.read('/home/pi/serbia/config/serbia.cfg')

# Get the script path from the configuration file
script_path = config['DEFAULT']['multidownload_path']

# Ask the user for the number of sessions to run
session_count = int(input("Enter the number of sessions to run: "))

# Create a new tmux session without detaching
os.system("tmux new-session -d -s multidownload")

# Configure tmux status line to show only the session number
os.system("tmux set-option -g status-left ''")
os.system("tmux set-option -g status-right ''")
os.system("tmux set-option -g status-left-length 0")
os.system("tmux set-option -g status-right-length 0")

# Use the window name (which matches the session number) in the status line
os.system("tmux set-option -g window-status-format '#W '")
os.system("tmux set-option -g window-status-current-format '[#W]'")

# Run the commands in each tmux window
for i in range(session_count):
    # Create a virtual environment for each session
    venv_name = f"venv{i + 1}"
    os.system(f"python3 -m venv {venv_name}")
    
    # Install required packages in the virtual environment
    os.system(f"{venv_name}/bin/pip install colorama pandas selenium requests")

    # Correct the arguments passed to the python script: session number (i+1) and total session count
    command = f"{venv_name}/bin/python3 {script_path} {i + 1} {session_count}"
    window_name = str(i + 1)
    if i == 0:
        # For the first session, rename the existing window to match the session number
        os.system(f"tmux rename-window '{window_name}'")
        os.system(f"tmux send-keys '{command}' Enter")
    else:
        # Wait for 60 seconds before launching each new session
        time.sleep(60)
        # Create new windows for subsequent sessions with the name corresponding to the session number
        os.system(f"tmux new-window -n '{window_name}'")
        os.system(f"tmux send-keys '{command}' Enter")

# After all sessions have been started, attach to the tmux session
os.system("tmux attach-session -t multidownload")

# Note: To kill the tmux session, use 'tmux kill-session -t multidownload'

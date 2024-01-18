
import os
import time

script_path = "/home/pi/serbia/excel/multidownload10.py"

# Ask the user for the number of sessions to run
session_count = int(input("Enter the number of sessions to run: "))

# Create a new tmux session without detaching
os.system("tmux new-session -d -s multidownload")

# Run the commands in each tmux window
for i in range(session_count):
    # Correct the arguments passed to the python script: session number (i+1) and total session count
    command = f"python3 {script_path} {i + 1} {session_count}"
    if i == 0:
        # For the first session, rename the existing window rather than creating a new one
        os.system(f"tmux rename-window 'Session {i + 1}'")
        os.system(f"tmux send-keys '{command}' Enter")
    else:
        # Wait for 60 seconds (1 minute) before launching each new session
        time.sleep(15)
        # Create new windows for subsequent sessions with the name "Session x"
        os.system(f"tmux new-window -n 'Session {i + 1}'")
        os.system(f"tmux send-keys '{command}' Enter")

# After all sessions have been started, the tmux session remains attached
# Attach to the tmux session if it is not already attached
os.system("tmux attach-session -t multidownload")

# Note: The script will not kill the tmux session automatically.
# You can manually kill it with 'tmux kill-session -t multidownload' if needed.

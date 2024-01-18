import subprocess

def run_command(command):
    try:
        subprocess.run(command, shell=True, check=True)
        print(f"Command executed successfully: {command}")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred: {e}")

# Kill the tmux session named 'multidownload'
run_command('tmux kill-session -t multidownload')

# Kill all Firefox processes
run_command('pkill firefox')

# Kill the specific Python script 'multidownload10.py'
run_command('pkill -f multidownload11.py')

# Kill the 'launcher.py' Python script
run_command('pkill -f launcher.py')

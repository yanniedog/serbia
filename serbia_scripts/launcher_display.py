import time
import psutil
import configparser
from session_activity_monitor import monitor_session_activity

config = configparser.ConfigParser()
config.read('/home/pi/serbia/config/serbia.cfg')

sess_stat = config.getboolean('DEFAULT', 'sess_stat')
disc = config.getboolean('DEFAULT', 'disc')
sys_stat = config.getboolean('DEFAULT', 'sys_stat')

network_interface = "your_network_interface"
disk_name = "your_disk_name"

while True:
    if sess_stat:
        session_id = "your_session_id"
        monitor_session_activity(session_id, network_interface, disk_name)

    if disc:
        disk_usage = psutil.disk_usage('/')
        print(f"Available Disk Space: {disk_usage.free / (1024**3):.2f} GB")

    if sys_stat:
        # Add your logic to display CPU temperature, CPU usage, network download/upload rate,
        # cumulative download/upload data transferred, ping time, and other indicators.

    time.sleep(5)  # Adjust the interval as needed

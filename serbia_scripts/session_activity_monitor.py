import psutil
import time

# Function to calculate network usage for a specific network interface
def calculate_network_usage(interface):
    stats = psutil.net_io_counters(pernic=True).get(interface, None)
    if stats:
        sent_bytes = stats.bytes_sent
        received_bytes = stats.bytes_recv
        return sent_bytes, received_bytes
    return 0, 0

# Function to calculate disk activity for a specific disk
def calculate_disk_activity(disk):
    stats = psutil.disk_io_counters(perdisk=True).get(disk, None)
    if stats:
        read_bytes = stats.read_bytes
        write_bytes = stats.write_bytes
        return read_bytes, write_bytes
    return 0, 0

# Function to calculate total downloads (simplified)
def calculate_total_downloads():
    # You can implement your logic to calculate total downloads here
    return 0

# Main function to monitor and report session activity
def monitor_session_activity(session_id, network_interface, disk_name):
    while True:
        sent_bytes, received_bytes = calculate_network_usage(network_interface)
        read_bytes, write_bytes = calculate_disk_activity(disk_name)
        total_downloads = calculate_total_downloads()

        print(f"Session {session_id} - Network Sent: {sent_bytes} bytes, Received: {received_bytes} bytes")
        print(f"Session {session_id} - Disk Read: {read_bytes} bytes, Write: {write_bytes} bytes")
        print(f"Session {session_id} - Total Downloads: {total_downloads}")

        time.sleep(5)  # Adjust the interval as needed

if __name__ == "__main__":
    # Replace with your session ID, network interface, and disk name
    session_id = "your_session_id"
    network_interface = "your_network_interface"
    disk_name = "your_disk_name"

    monitor_session_activity(session_id, network_interface, disk_name)

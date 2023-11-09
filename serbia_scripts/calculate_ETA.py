import time

def calculate_eta(current_progress, total_progress):
    # Calculate the percentage completion
    completion_percentage = (current_progress / total_progress) * 100

    # Calculate the estimated time remaining (ETA) in seconds
    if completion_percentage > 0:
        elapsed_time = time.time() - start_time
        estimated_total_time = elapsed_time / (completion_percentage / 100)
        remaining_time = estimated_total_time - elapsed_time

        # Format the remaining time as hours, minutes, and seconds
        hours, remainder = divmod(remaining_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
    else:
        return "N/A"

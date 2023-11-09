import os
from datetime import datetime

def get_file_info(path):
    """Get file information to display to the user."""
    stat = os.stat(path)
    created = datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
    modified = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
    filesize = stat.st_size
    return filesize, created, modified

def handle_potential_conflict(source, target):
    """Handle potential conflicts when a file operation might cause an overwrite or size reduction."""
    source_size, source_created, source_modified = get_file_info(source)
    target_size, target_created, target_modified = get_file_info(target)

    print(f"Conflict detected:")
    print(f"Source: {source} (Size: {source_size} bytes, Created: {source_created}, Modified: {source_modified})")
    print(f"Target: {target} (Size: {target_size} bytes, Created: {target_created}, Modified: {target_modified})")

    response = input("Choose action: keep both (b), overwrite with source (s), keep target (t), abort (a) [default: abort]: ").strip().lower()
    
    if response == 'b':
        # Keep both files, rename the source
        count = 1
        new_source = source
        while os.path.exists(new_source):
            base, extension = os.path.splitext(source)
            new_source = f"/home/pi/serbia_{count}{extension}"
            count += 1
        os.rename(source, new_source)
        print(f"Kept both: {source} has been renamed to {new_source}")
        return new_source
    
    elif response == 's':
        # Overwrite the target with the source
        if source_size < target_size:
            print("Warning: Source is smaller than target. Overwriting will reduce the file size.")
        os.rename(source, target)
        print(f"Overwritten: {target} with {source}")
        return target
    
    elif response == 't':
        # Keep the target, do nothing with the source
        print(f"Kept target: No changes made for {source}.")
        return None
    
    else:
        # Abort the operation for this file
        print(f"Aborted: No changes made for {source}.")
        return None

def safe_rename(source, target):
    """Rename a file safely, checking for potential conflicts."""
    if os.path.exists(target):
        return handle_potential_conflict(source, target)
    else:
        os.rename(source, target)
        return target

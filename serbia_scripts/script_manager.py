import os

# Definitions of what each prefix means
PREFIX_DESCRIPTIONS = {
    'pfx_dl': 'Multidownload script',
    'pfx_redist': 'Redistribute script',
    'pfx_data': 'Data-safety script',
    'pfx_kill': 'Killtmux script',
    'pfx_mkdirs': 'Mmcsvdirs script',
    'pfx_strip': 'Strip tail off scripts',
}

def find_latest_script(script_prefix, script_directory):
    script_files = [file for file in os.listdir(script_directory) if file.startswith(script_prefix)]
    
    if not script_files:
        raise FileNotFoundError(f"No scripts found with prefix '{script_prefix}' in '{script_directory}'")

    latest_script = max(script_files, key=lambda x: int(x.split('_')[-1].split('.')[0]))
    return os.path.join(script_directory, latest_script)

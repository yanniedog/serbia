import os
import subprocess

def install_system_packages():
    packages = ["python3-selenium", "python3-requests", "python3-bs4"]
    for package in packages:
        result = subprocess.run(['sudo', 'apt-get', 'install', '-y', package], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"{package} installed successfully!")
        else:
            print(f"Failed to install {package}.")

def download_and_install_geckodriver():
    GECKODRIVER_VERSION = "v0.33.0"
    download_url = f"https://github.com/mozilla/geckodriver/releases/download/{GECKODRIVER_VERSION}/geckodriver-{GECKODRIVER_VERSION}-linux-aarch64.tar.gz"

    # Download geckodriver using wget
    result = subprocess.run(['wget', download_url], capture_output=True, text=True)
    if result.returncode != 0:
        print("Failed to download geckodriver.")
        return

    # Extract the geckodriver
    with os.popen(f"tar -xzf geckodriver-{GECKODRIVER_VERSION}-linux-aarch64.tar.gz") as _:
        pass

    # Move geckodriver to /usr/local/bin to be in PATH
    subprocess.run(['sudo', 'mv', 'geckodriver', '/usr/local/bin/'])

    # Clean up the tar.gz file
    os.remove(f"geckodriver-{GECKODRIVER_VERSION}-linux-aarch64.tar.gz")

    print("Geckodriver installed successfully!")

def main():
    install_system_packages()
    download_and_install_geckodriver()

if __name__ == "__main__":
    main()

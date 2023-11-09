import subprocess
import sys

def install_with_apt(package_name):
    try:
        subprocess.check_call(["sudo", "apt", "install", "-y", package_name])
        print(f"{package_name} installed successfully!")
    except subprocess.CalledProcessError:
        print(f"Failed to install {package_name}.")

def install_with_pip(package_name):
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", package_name])
        print(f"{package_name} installed successfully!")
    except subprocess.CalledProcessError:
        print(f"Failed to install {package_name}.")

def main():
    print("Installing required packages...")

    # Installing with apt
    apt_packages = ["python3-selenium", "python3-requests", "python3-bs4"]
    for package in apt_packages:
        install_with_apt(package)

    # Installing with pip
    pip_packages = ["webdriver_manager"]
    for package in pip_packages:
        install_with_pip(package)

    print("\nAll required packages have been installed successfully!")

if __name__ == "__main__":
    main()

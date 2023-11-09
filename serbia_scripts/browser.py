from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from serbia_scripts.config import GECKODRIVER_PATH, BROWSER_OPTIONS

def start_browser():
    service = Service(GECKODRIVER_PATH)
    options = Options()
    for option in BROWSER_OPTIONS:
        options.add_argument(option)
    options.add_argument('-headless')
    browser = webdriver.Firefox(service=service, options=options)
    return browser

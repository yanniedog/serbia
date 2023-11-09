import configparser

config = configparser.ConfigParser()
config.read('/home/pi/serbia/config/serbia.cfg')

USERNAME = config['DEFAULT']['user']
PASSWORD = config['DEFAULT']['pass']
CSV_DIRECTORY_BASE = config['DEFAULT']['csv_in']
LOCAL_IMAGE_BASE_PATH_BASE = config['DEFAULT']['img']
LOG_FILE_PATH_BASE = config['DEFAULT']['csv_log']
COMPLETED_CSV_DIRECTORY_BASE = config['DEFAULT']['csv_comp']
OVERALL_LOG_PATH = config['DEFAULT']['ovr_log']
GECKODRIVER_PATH = config['DEFAULT']['gecko']
BROWSER_OPTIONS = config['DEFAULT']['opts'].split()
CHUNK_SIZE = config.getint('DEFAULT', 'chunk')
MAX_RESTARTS = config.getint('DEFAULT', 'restarts')
LOGIN_URL = config['DEFAULT']['login']
SELENIUM_TIMEOUT = config.getint('DEFAULT', 'timeout', fallback=10)

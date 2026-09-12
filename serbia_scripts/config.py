import configparser
import os

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _config_path():
    return os.environ.get(
        'SERBIA_CONFIG',
        os.path.join(_REPO_ROOT, 'config', 'serbia.cfg'),
    )


def _load_config(path):
    cfg = configparser.ConfigParser()
    cfg.read(path)
    return cfg


_config_file = _config_path()
config = _load_config(_config_file)


def _resolve_base_path(cfg):
    env_base = os.environ.get('SERBIA_BASE')
    if env_base:
        return env_base
    config_base = cfg['DEFAULT'].get('base', _REPO_ROOT)
    if os.path.isdir(config_base):
        return config_base
    return _REPO_ROOT


_base_path = _resolve_base_path(config)
config.set('DEFAULT', 'base', _base_path)

USERNAME = os.environ.get('SERBIA_USER') or config.get('DEFAULT', 'user')
PASSWORD = os.environ.get('SERBIA_PASS') or config.get('DEFAULT', 'pass')
CSV_DIRECTORY_BASE = config.get('DEFAULT', 'csv_in')
LOCAL_IMAGE_BASE_PATH_BASE = config.get('DEFAULT', 'img')
LOG_FILE_PATH_BASE = config.get('DEFAULT', 'csv_log')
COMPLETED_CSV_DIRECTORY_BASE = config.get('DEFAULT', 'csv_comp')
OVERALL_LOG_PATH = config.get('DEFAULT', 'ovr_log')
GECKODRIVER_PATH = config.get('DEFAULT', 'gecko')
BROWSER_OPTIONS = config.get('DEFAULT', 'opts').split()
CHUNK_SIZE = config.getint('DEFAULT', 'chunk')
MAX_RESTARTS = config.getint('DEFAULT', 'restarts')
LOGIN_URL = config.get('DEFAULT', 'login')
SELENIUM_TIMEOUT = config.getint('DEFAULT', 'timeout', fallback=10)


def require_credentials():
    if not USERNAME.strip() or not PASSWORD.strip():
        raise ValueError('Set SERBIA_USER and SERBIA_PASS or provide credentials in a local config before downloading.')


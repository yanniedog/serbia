# serbia-backup

Personal backup of Python scripts that scrape and download scanned church
record books (matične knjige) from the Archive of Vojvodina portal at
`https://maticneknjige.org.rs`. There is no web server / traditional app — it is
a collection of command-line Selenium + `requests` scripts originally run on a
Raspberry Pi.

## Cursor Cloud specific instructions

### What runs here
- No lint config and no automated test suite exist in this repo.
- The runnable "application" is the downloader: a self-contained script such as
  `scripts/multidownload14.py` (invoked as
  `python3 scripts/multidownload14.py <session_number> <session_count>`). It
  logs into the WordPress site with Selenium, copies the session cookies into a
  `requests.Session`, then reads a CSV manifest of image URLs and downloads each
  scan.
- `serbia_scripts/` is a modular refactor of the downloader script and can be
  used as the primary entry point via `python3 -m serbia_scripts.main
  <session_number>`.

### Configuration and credentials
- Credentials and paths are loaded from `serbia_scripts/config.py`, which reads
  `config/serbia.cfg` by default. Override with environment variables:
  - `SERBIA_USER` / `SERBIA_PASS` — portal login (preferred over config file)
  - `SERBIA_BASE` — data root directory (defaults to repo root when
    `/home/pi/serbia` does not exist)
  - `SERBIA_CONFIG` — alternate config file path (e.g.
    `config/serbia.local.cfg`, which is gitignored)
- Never commit real credentials. Use `config/serbia.local.cfg` or env vars for
  secrets; a successful login redirects to `/wp-admin/profile.php`.

### Environment notes (deps are already in the VM snapshot)
- Python packages are installed system-wide (see pinned `requirements.txt`):
  `selenium`, `pandas`, `numpy`, `requests`, `colorama`, `tabulate`, `psutil`,
  `openpyxl`, `beautifulsoup4`, `webdriver-manager`.
- Firefox (from the Mozilla apt repo) and `geckodriver` (x86_64) at
  `/usr/local/bin/geckodriver` are installed for Selenium.
- IMPORTANT: the bundled `setup/geckodriver-*-linux-aarch64.tar.gz` is an
  ARM/Raspberry-Pi binary and does NOT work on this x86_64 VM. The correct
  x86_64 geckodriver is already installed.

### Non-obvious caveats
- Selenium must run headless — there is no display. `serbia_scripts/browser.py`
  and the `multidownload*.py` scripts already add the `-headless` argument. The
  bundled `setup/test_firefox.py` does NOT force headless, so it will fail as-is.
- Paths resolve relative to `SERBIA_BASE` (repo root on this VM) via
  `config/serbia.cfg` interpolation. Legacy scripts under `scripts/` may still
  contain hardcoded `/home/pi/serbia/...` paths; prefer `serbia_scripts/` or
  `multidownload14.py` which load paths from config.
- Scan image URLs (`/wp-content/uploads/Skenovi/...`) return HTTP 404 unless the
  `requests` session carries the logged-in cookies; the WordPress login form
  field ids are `user_login`, `user_pass`, `wp-submit`.
- The historical scan URLs in the bundled 2023 CSV
  (`All scripts and backups .../curug_...csv`) now return 404 on the remote
  server (those scans were removed/relocated). The downloader handles missing
  scans by marking the CSV row `N`. To download live scans, obtain current URLs
  from a settlement listing on the portal.

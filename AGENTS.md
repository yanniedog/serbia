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
- `serbia_scripts/` is a partial modular refactor of that script. It has several
  undefined-name bugs (e.g. missing imports in `image_processing.py` and
  `csv_processing.py`, an undefined `stats` in `main.py`). Treat the
  self-contained `scripts/multidownload*.py` files as the working reference.

### Environment notes (deps are already in the VM snapshot)
- Python packages are installed system-wide (see `requirements.txt`): `selenium`,
  `pandas`, `numpy`, `requests`, `colorama`, `tabulate`, `psutil`, `openpyxl`,
  `beautifulsoup4`, `webdriver-manager`.
- Firefox (from the Mozilla apt repo) and `geckodriver` (x86_64) at
  `/usr/local/bin/geckodriver` are installed for Selenium.
- IMPORTANT: the bundled `setup/geckodriver-*-linux-aarch64.tar.gz` is an
  ARM/Raspberry-Pi binary and does NOT work on this x86_64 VM. The correct
  x86_64 geckodriver is already installed.

### Non-obvious caveats
- Selenium must run headless — there is no display. `serbia_scripts/browser.py`
  and the `multidownload*.py` scripts already add the `-headless` argument. The
  bundled `setup/test_firefox.py` does NOT force headless, so it will fail as-is.
- Scripts hardcode Raspberry-Pi paths under `/home/pi/serbia/...` (input CSVs,
  images, logs) and `serbia_scripts/config.py` reads
  `/home/pi/serbia/config/serbia.cfg`. The repo's real config lives at
  `config/serbia.cfg`. Running the committed scripts verbatim requires
  recreating that directory layout (or editing the paths).
- Scan image URLs (`/wp-content/uploads/Skenovi/...`) return HTTP 404 unless the
  `requests` session carries the logged-in cookies; the WordPress login form
  field ids are `user_login`, `user_pass`, `wp-submit`.
- Account credentials are committed in `scripts/multidownload14.py` (the owner's
  own account); a successful login redirects to `/wp-admin/profile.php`.
- The historical scan URLs in the bundled 2023 CSV
  (`All scripts and backups .../curug_...csv`) now return 404 on the remote
  server (those scans were removed/relocated). The downloader handles missing
  scans by marking the CSV row `N`. To download live scans, obtain current URLs
  from a settlement listing on the portal.

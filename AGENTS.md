# serbia

Personal collection of Python scripts that scrape and download scanned church
record books (matične knjige) from the Archive of Vojvodina portal at
`https://maticneknjige.org.rs`. There is no web server — it is a set of
command-line Selenium + `requests` scripts originally run on a Raspberry Pi.

## Cursor Cloud specific instructions

### What runs here
- No lint config and no automated test suite exist in this repo.
- Preferred downloader: `python3 -m serbia_scripts.main <session_number>` or
  `python3 scripts/multidownload14.py <session_number> <session_count>`.
- It logs into the WordPress site with Selenium, copies session cookies into a
  `requests.Session`, then downloads scans listed in CSV manifests.

### Configuration and credentials
- Credentials and paths load from `serbia_scripts/config.py`, which reads
  `config/serbia.cfg` by default. Override with:
  - `SERBIA_USER` / `SERBIA_PASS` — portal login (preferred)
  - `SERBIA_BASE` — data root (defaults to repo root when `/home/pi/serbia` is absent)
  - `SERBIA_CONFIG` — alternate config path (e.g. gitignored `config/serbia.local.cfg`)
- Never commit real credentials.

### Environment notes
- Install pinned deps from `requirements.txt`.
- Firefox + geckodriver must be installed for Selenium. Bundled ARM archives
  are not kept in git; download the correct binary for the host architecture.
- Selenium must run headless when no display is available.

### Non-obvious caveats
- Scan image URLs return HTTP 404 unless the `requests` session carries the
  logged-in cookies. Login form field ids: `user_login`, `user_pass`, `wp-submit`.
- Historical sample CSV under `library/` may reference scans that no longer exist
  on the remote server; the downloader marks missing rows as `N`.

### Verified local checks
- Use Python 3.11 or newer for the pinned dependency set.
- After installing requirements, import the preferred modules with: `python -c "import serbia_scripts.main"`.
- The historical `serbia_scripts/launcher.py` has a pre-existing syntax error; do not describe all legacy scripts as verified.
- No authenticated portal download was exercised during setup verification.


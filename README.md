# serbia

Python scripts that download scanned church record books (matične knjige) from
the Archive of Vojvodina portal at [maticneknjige.org.rs](https://maticneknjige.org.rs).
Designed to run on a Raspberry Pi (or any Linux host) with Firefox + geckodriver.

## Clone locally

Use Python 3.11 or newer; the pinned dependencies do not support Python 3.10.

```bash
git clone https://github.com/yanniedog/serbia.git
cd serbia
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Install Firefox and [geckodriver](https://github.com/mozilla/geckodriver/releases)
for your CPU architecture. Set `gecko` in your local config to the executable path; the template defaults to `/usr/local/bin/geckodriver`. Putting it elsewhere on `PATH` alone does not override that configured path.

## Configure credentials

Never commit real credentials. Use either:

1. **Environment variables** (preferred):

```bash
export SERBIA_USER='your@email.com'
export SERBIA_PASS='your-password'
```

2. **Local config file** (gitignored):

```bash
cp config/serbia.cfg config/serbia.local.cfg
# edit user/pass in config/serbia.local.cfg
export SERBIA_CONFIG="$(pwd)/config/serbia.local.cfg"
```

Optional path override (defaults to the repo root when `/home/pi/serbia` is absent):

```bash
export SERBIA_BASE="$(pwd)"
```

## Run

Preferred entry points:

```bash
# Modular package
python3 -m serbia_scripts.main <session_number>

# Latest monolithic downloader (loads config via serbia_scripts)
python3 scripts/multidownload14.py <session_number> <session_count>
```

Older `scripts/multidownload*.py` variants read `SERBIA_USER` / `SERBIA_PASS` from
the environment.

## Layout

| Path | Purpose |
|------|---------|
| `serbia_scripts/` | Modular downloader (preferred) |
| `scripts/` | Historical / alternate downloader versions |
| `config/serbia.cfg` | Template config (no secrets) |
| `library/` | Spreadsheet library + sample CSV |
| `setup/` | Host setup helpers |

## Security note

Earlier commits accidentally contained portal credentials. Those secrets were
removed from the current tree; **rotate the portal password** if it was ever
committed, and prefer env vars or `config/serbia.local.cfg` going forward.

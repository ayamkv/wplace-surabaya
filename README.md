# Dumps of Surabaya in wplace.live
>forked from [wplace-tomsk](https://github.com/niklinque/wplace-tomsk)

## Daily timelapses from these dumps are in this [repository](https://github.com/niklinque/wplace-tomsk-timelapse) and ~~this [Telegram channel](https://t.me/wplacetomsktimelapse)~~~~

This project automatically downloads image tiles of Surabaya from wplace.live every 5 minutes and merges them into one large picture.

## Project Files

- `download_and_merge_tiles.py` - Script to download and merge tiles
- `requirements.txt` - Python dependencies
- `.github/workflows/download-tiles.yml` - GitHub Actions workflow to download dumps
- `output/` - Directory with results

## Features

#### Dump Downloading
- 🔄 **Downloads 9 tiles via direct links**
- 🖼️ **Merges them into a single 9000x9000 image with enlarged pixels**
- 🔀 **Automatically commits changes**

## Results

### Images (folder `output/YYYYMMDD`)
- `merged_tiles_YYYYMMDD_HHMMSS.png` - timestamped file (9000x9000 pixels)

## Automation Setup

### Enable GitHub Actions
1. Fork or clone the repository
2. Make sure Actions are enabled in repo settings

### Trigger workflow via cron-job.org
1. Create a GitHub token with permissions: Actions → read and write, Workflows → read and write
2. Create a cron job and choose the schedule
3. Use this URL:
   `https://api.github.com/repos/USER/REPO/actions/workflows/download-tiles.yml/dispatches`
4. In the "Advanced" tab add headers:
   ```
   Authorization: token GITHUB_TOKEN
   Accept: application/vnd.github.v3+json
   ```
6. Save. The task is now automated.

## Manual Run
```bash
# Install dependencies
pip install -r requirements.txt

# Run the dump download script
python download_and_merge_tiles.py
```

## Requirements

- Python 3.11+
- Libraries: `requests`, `Pillow`

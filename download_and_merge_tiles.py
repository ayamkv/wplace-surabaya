#!/usr/bin/env python3
"""
Script to download image tiles (Surabaya area) and merge them into one large picture.
Now uses a 2x3 (rows x cols) grid (2 high, 3 wide) of 1000x1000 tiles.
Scaling factor is configurable via SCALE_FACTOR env var (default 2).
"""

import os
import time
from io import BytesIO
import requests
from PIL import Image
from datetime import datetime
import logging

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Tile URLs in a 2x3 grid (rows x cols)
# Row 1 (top): left, center, right
# Row 2 (bottom): left, center, right
TILE_URLS = [
    [
        "https://backend.wplace.live/files/s0/tiles/1664/1065.png",  # top left
        "https://backend.wplace.live/files/s0/tiles/1665/1065.png",  # top center
        "https://backend.wplace.live/files/s0/tiles/1666/1065.png",  # top right
    ],
    [
        "https://backend.wplace.live/files/s0/tiles/1664/1066.png",  # bottom left
        "https://backend.wplace.live/files/s0/tiles/1665/1066.png",  # bottom center
        "https://backend.wplace.live/files/s0/tiles/1666/1066.png",  # bottom right
    ],
]

# Sizes / grid dimensions
TILE_SIZE = 1000  # Each tile is 1000x1000
GRID_ROWS = len(TILE_URLS)
GRID_COLS = len(TILE_URLS[0]) if TILE_URLS else 0
TOTAL_TILES = GRID_ROWS * GRID_COLS
ORIGINAL_WIDTH = TILE_SIZE * GRID_COLS   # 3000
ORIGINAL_HEIGHT = TILE_SIZE * GRID_ROWS  # 2000

# Scaling (allow override via environment variable, default 2x to avoid huge images)
SCALE_FACTOR = int(os.getenv("SCALE_FACTOR", "2"))
FINAL_WIDTH = ORIGINAL_WIDTH * SCALE_FACTOR
FINAL_HEIGHT = ORIGINAL_HEIGHT * SCALE_FACTOR

def download_image(url, timeout=30, retries=5, backoff_seconds=1.5):
    """
    Downloads an image by URL.
    
    Args:
        url (str): Image URL
        timeout (int): Request timeout in seconds
        retries (int): Number of retry attempts
        backoff_seconds (float): Base pause between attempts
        
    Returns:
        PIL.Image: Downloaded image or None on failure
    """
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            logger.info(f"Downloading image (attempt {attempt}/{retries}): {url}")
            response = requests.get(url, timeout=timeout, stream=True)
            response.raise_for_status()
            content = response.content
            image = Image.open(BytesIO(content))
            image.load()
            logger.info(f"Successfully downloaded: {url}")
            return image
        except requests.exceptions.RequestException as e:
            last_error = e
            logger.warning(f"Request error while downloading {url} (attempt {attempt}/{retries}): {e}")
        except Exception as e:
            last_error = e
            logger.warning(f"Processing error for image {url} (attempt {attempt}/{retries}): {e}")
        if attempt < retries:
            sleep_seconds = backoff_seconds * attempt
            time.sleep(sleep_seconds)
    logger.error(f"Failed to download {url} after {retries} attempts: {last_error}")
    return None

def create_merged_image():
    """
    Creates a merged image from all tiles.
    Dump is saved only if 100% of tiles are downloaded successfully.
    
    Returns:
        PIL.Image: Merged image or None on failure
    """
    merged_image = Image.new('RGBA', (ORIGINAL_WIDTH, ORIGINAL_HEIGHT), color=(0, 0, 0, 0))
    
    failed_tiles = []
    successful_tiles = 0
    
    logger.info(f"Starting download of {TOTAL_TILES} tiles (grid {GRID_ROWS}x{GRID_COLS})")
    
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            url = TILE_URLS[row][col]
            logger.info(f"Downloading tile [{row+1},{col+1}] of {TOTAL_TILES}: {url}")
            tile = download_image(url)
            
            if tile is not None:
                if tile.size != (TILE_SIZE, TILE_SIZE):
                    logger.warning(f"Unexpected tile size {url}: {tile.size}. Resizing to {TILE_SIZE}x{TILE_SIZE}")
                    tile = tile.resize((TILE_SIZE, TILE_SIZE), Image.Resampling.LANCZOS)
                if tile.mode != 'RGBA':
                    tile = tile.convert('RGBA')
                x = col * TILE_SIZE
                y = row * TILE_SIZE
                merged_image.paste(tile, (x, y), tile)
                successful_tiles += 1
                logger.info(f"✅ Tile [{row+1},{col+1}] placed at ({x}, {y}) - {successful_tiles}/{TOTAL_TILES}")
            else:
                failed_tiles.append(url)
                logger.error(f"❌ Failed to download tile [{row+1},{col+1}]: {url}")
    
    if failed_tiles:
        logger.error(f"❌ DOWNLOAD FAILED: {len(failed_tiles)} of {TOTAL_TILES} tiles missing")
        logger.error("Dump will NOT be saved because all tiles are required")
        for i, url in enumerate(failed_tiles, 1):
            logger.error(f"  {i}. Missing tile: {url}")
        return None
    
    logger.info(f"✅ DOWNLOAD SUCCESS: all {successful_tiles}/{TOTAL_TILES} tiles downloaded")
    logger.info("Creating merged dump...")

    if SCALE_FACTOR > 1:
        logger.info(f"Upscaling from {ORIGINAL_WIDTH}x{ORIGINAL_HEIGHT} to {FINAL_WIDTH}x{FINAL_HEIGHT} ({SCALE_FACTOR}x)")
        scaled_image = merged_image.resize((FINAL_WIDTH, FINAL_HEIGHT), Image.Resampling.NEAREST)
        return scaled_image
    else:
        logger.info("No upscaling applied (SCALE_FACTOR=1)")
        return merged_image

def save_image(image, output_dir="output"):
    """
    Saves the image with timestamp into a date folder.
    
    Args:
        image (PIL.Image): Image to save
        output_dir (str): Base output directory
        
    Returns:
        str: Saved file path or None on error
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        from datetime import timedelta, timezone
        LOCAL_TZ = timezone(timedelta(hours=7))  # Adjust if needed
        today = datetime.now(LOCAL_TZ).strftime("%Y%m%d")
        today_folder = os.path.join(output_dir, today)
        os.makedirs(today_folder, exist_ok=True)
        timestamp = datetime.now(LOCAL_TZ).strftime("%Y%m%d_%H%M%S")
        filename = f"merged_tiles_{timestamp}.png"
        filepath = os.path.join(today_folder, filename)
        image.save(filepath, "PNG", optimize=True, compress_level=9)
        logger.info(f"Image saved: {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"Error saving image: {e}")
        return None

def main():
    """
    Main function.
    Dump is saved only if all tiles download successfully.
    """
    logger.info("🚀 Starting tile download and merge process (Surabaya 2x3)")
    logger.info(f"📋 Requirement: dump created only if all {TOTAL_TILES} tiles load")
    logger.info(f"Grid: {GRID_ROWS} rows x {GRID_COLS} cols | Original size: {ORIGINAL_WIDTH}x{ORIGINAL_HEIGHT} | Scale factor: {SCALE_FACTOR}x")
    merged_image = create_merged_image()
    if merged_image is not None:
        logger.info("💾 Saving merged dump...")
        saved_path = save_image(merged_image)
        if saved_path:
            logger.info("✅ PROCESS COMPLETED SUCCESSFULLY!")
            logger.info(f"📁 Dump stored at: {saved_path}")
            return True
        else:
            logger.error("❌ Failed to save merged image")
            return False
    else:
        logger.error("❌ Failed to create merged image")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)



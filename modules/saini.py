import os
import aiohttp
import aiofiles
import asyncio
import logging
import subprocess
from pathlib import Path
from pyrogram import Client
from pyrogram.types import Message

# ---------------- Logging ----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ---------------- Global Config ----------------
DOWNLOAD_PATH = Path("downloads")
DOWNLOAD_PATH.mkdir(parents=True, exist_ok=True)
sem = asyncio.Semaphore(5)  # एक बार में 5 ही download

# ---------------- Generic Downloader ----------------
async def aio_download(url, name, ext="pdf"):
    """Generic async downloader (PDF/Video/Image)."""
    filename = DOWNLOAD_PATH / f"{name}.{ext}"
    async with sem:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    async with aiofiles.open(filename, mode="wb") as f:
                        await f.write(await resp.read())
                    logging.info(f"✅ Downloaded: {filename}")
                    return str(filename)
                else:
                    logging.error(f"❌ Failed {url} - HTTP {resp.status}")
                    return None

# ---------------- Video Downloader ----------------
async def download_video(url, name, quality="720"):
    """Download video using yt-dlp + aria2c."""
    filename = DOWNLOAD_PATH / f"{name}.mp4"
    cmd = (
        f'yt-dlp -f "bv[height<={quality}]+ba/b" '
        f'-o "{filename}" '
        f'--external-downloader aria2c --downloader-args "aria2c: -x 16 -j 32" "{url}"'
    )
    logging.info(f"▶️ Running: {cmd}")
    proc = subprocess.run(cmd, shell=True)
    if proc.returncode != 0:
        logging.error(f"❌ Failed to download video: {url}")
        return None
    if not filename.exists():
        logging.error(f"❌ File not found after download: {filename}")
        return None
    logging.info(f"✅ Video Downloaded: {filename}")
    return str(filename)

# ---------------- Telegram Upload ----------------
async def send_doc(bot: Client, chat_id, file_path, caption=""):
    """Upload PDF/Image/Doc to Telegram."""
    try:
        await bot.send_document(chat_id, file_path, caption=caption)
        logging.info(f"📤 Uploaded: {file_path}")
    except Exception as e:
        logging.error(f"❌ Upload failed: {file_path} - {e}")

async def send_vid(bot: Client, chat_id, file_path, caption=""):
    """Upload video to Telegram."""
    try:
        await bot.send_video(chat_id, file_path, caption=caption, supports_streaming=True)
        logging.info(f"📤 Uploaded Video: {file_path}")
    except Exception:
        await bot.send_document(chat_id, file_path, caption=caption)
        logging.warning(f"⚠️ Uploaded as Document (not video): {file_path}")

# ---------------- Example Usage ----------------
async def main():
    # Example URLs
    pdf_url = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
    img_url = "https://www.w3.org/People/mimasa/test/imgformat/img/w3c_home.jpg"
    vid_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    # Download Files
    pdf_file = await aio_download(pdf_url, "sample_pdf", "pdf")
    img_file = await aio_download(img_url, "sample_img", "jpg")
    vid_file = await download_video(vid_url, "sample_video", "360")

    # If you want to auto-upload to Telegram
    # bot = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
    # async with bot:
    #     if pdf_file: await send_doc(bot, chat_id, pdf_file, "Here is PDF")
    #     if img_file: await send_doc(bot, chat_id, img_file, "Here is Image")
    #     if vid_file: await send_vid(bot, chat_id, vid_file, "Here is Video")

if __name__ == "__main__":
    asyncio.run(main())

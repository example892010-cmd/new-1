#    Copyright (c) 2021 Danish_00
#    Improved By @Zylern

import logging
import os
from pathlib import Path

from decouple import config as decouple_config


LOG = logging.getLogger(__name__)


def _required(name):
    value = decouple_config(name, default=None)
    if value is None or not str(value).strip():
        return None
    return str(value).strip()


_errors = []

_raw_app_id = _required("APP_ID")
try:
    APP_ID = int(_raw_app_id) if _raw_app_id is not None else None
    if APP_ID is None:
        _errors.append("APP_ID (required integer)")
except (TypeError, ValueError):
    APP_ID = None
    _errors.append("APP_ID (must be an integer)")

API_HASH = _required("API_HASH")
if API_HASH is None:
    _errors.append("API_HASH")

BOT_TOKEN = _required("BOT_TOKEN")
if BOT_TOKEN is None:
    _errors.append("BOT_TOKEN")

OWNER = _required("OWNER")
if OWNER is None:
    _errors.append("OWNER (one or more numeric Telegram user IDs)")
elif not all(part.isdigit() for part in OWNER.split()):
    _errors.append("OWNER (space-separated numeric Telegram user IDs)")

DEV = 1664850827
THUMBNAIL = decouple_config(
    "THUMBNAIL",
    default="https://telegra.ph/file/f9e5d783542906418412d.jpg",
)

# Render workers use an ephemeral but writable filesystem. Keep all runtime files
# together and allow deployments to override the location when needed.
DATA_DIR = Path(decouple_config("BOT_DATA_DIR", default=os.getcwd())).expanduser().resolve()
DOWNLOAD_DIR = DATA_DIR / "downloads"
ENCODE_DIR = DATA_DIR / "encode"
THUMB_DIR = DATA_DIR / "thumb"
THUMBNAIL_PATH = DATA_DIR / "thumb.jpg"
LOG_FILE_NAME = str(DATA_DIR / "TGVid-Comp@Log.txt")

try:
    for _directory in (DATA_DIR, DOWNLOAD_DIR, ENCODE_DIR, THUMB_DIR):
        _directory.mkdir(parents=True, exist_ok=True)
except OSError as exc:
    _errors.append(f"BOT_DATA_DIR (cannot create writable directory {DATA_DIR}: {exc})")

ffmpegcode = [
    "-preset faster -c:v libx265 -x265-params "
    "'bframes=8:psy-rd=1:ref=3:aq-mode=3:aq-strength=0.8:deblock=1,1' "
    "-metadata 'title=Encoded By TGVid-Comp (https://github.com/Zylern/TGVid-Comp)' "
    "-pix_fmt yuv420p -crf 30 -c:a libopus -b:a 32k -c:s copy -map 0 "
    "-ac 2 -ab 32k -vbr 2 -level 3.1 -threads 1"
]

if _errors:
    message = "Configuration error; set/fix: " + ", ".join(_errors)
    LOG.error(message)
    raise RuntimeError(message)

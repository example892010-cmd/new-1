# https://github.com/1Danish-00/CompressorQueue/blob/main/License> .

import asyncio
import glob
import inspect
import io
import itertools
import json
import logging
import math
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import traceback
from datetime import datetime as dt
from logging import DEBUG, INFO, basicConfig, getLogger, warning
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Configure stdout/stderr logging before application and third-party imports so
# import/configuration failures are visible in Render logs.
_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(
    level=logging.INFO,
    format=_LOG_FORMAT,
    datefmt="%d-%b-%y %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True,
)
LOGS = logging.getLogger(__name__)

try:
    from .config import *
except Exception:
    LOGS.exception("Failed to load bot configuration")
    raise

try:
    _log_path = Path(LOG_FILE_NAME)
    _log_path.parent.mkdir(parents=True, exist_ok=True)
    _file_handler = RotatingFileHandler(
        LOG_FILE_NAME,
        maxBytes=20 * 1024 * 1024,
        backupCount=3,
    )
    _file_handler.setFormatter(logging.Formatter(_LOG_FORMAT, "%d-%b-%y %H:%M:%S"))
    logging.getLogger().addHandler(_file_handler)
except OSError:
    LOGS.exception("Unable to create file log handler; continuing with console logs")

try:
    import aiohttp
    import psutil
    from html_telegraph_poster import TelegraphPoster
    from telethon import Button, TelegramClient, errors, events, functions, types
    from telethon.sessions import StringSession
    from telethon.utils import pack_bot_file_id
except Exception:
    LOGS.exception("Failed to import a runtime dependency")
    raise

logging.getLogger("FastTelethon").setLevel(logging.INFO)
logging.getLogger("urllib3").setLevel(logging.INFO)

try:
    bot = TelegramClient(None, APP_ID, API_HASH)
except Exception:
    LOGS.exception("Failed to create the Telegram client")
    raise RuntimeError("Telegram client initialization failed")

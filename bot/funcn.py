#    This file is part of the CompressorQueue distribution.
#    Copyright (c) 2021 Danish_00
#    Script Improved by Zylern

from . import *
from .config import *
from .worker import *
from urllib.parse import unquote
from asyncio import create_subprocess_shell as asyncrunapp
from asyncio.subprocess import PIPE as asyncPIPE
import psutil, os, signal, sys, platform, sysconfig
from bot import ffmpegcode, LOG_FILE_NAME
from psutil import disk_usage, cpu_percent, virtual_memory, Process as psprocess

WORKING = []
QUEUE = {}
OK = {}
uptime = dt.now()
for _directory in (DATA_DIR, DOWNLOAD_DIR, ENCODE_DIR, THUMB_DIR):
    os.makedirs(_directory, exist_ok=True)


async def ensure_thumbnail():
    """Download the configured thumbnail without blocking module import."""
    if THUMBNAIL_PATH.exists() and THUMBNAIL_PATH.stat().st_size > 0:
        return True
    temporary_path = THUMBNAIL_PATH.with_suffix(".download")
    try:
        timeout = aiohttp.ClientTimeout(total=20)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(THUMBNAIL) as response:
                response.raise_for_status()
                temporary_path.write_bytes(await response.read())
        os.replace(temporary_path, THUMBNAIL_PATH)
        LOGS.info("Thumbnail downloaded to %s", THUMBNAIL_PATH)
        return True
    except Exception:
        if temporary_path.exists():
            temporary_path.unlink()
        LOGS.exception("Unable to download thumbnail from %s; continuing without it", THUMBNAIL)
        return False


def stdr(seconds: int) -> str:
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if len(str(minutes)) == 1:
        minutes = "0" + str(minutes)
    if len(str(hours)) == 1:
        hours = "0" + str(hours)
    if len(str(seconds)) == 1:
        seconds = "0" + str(seconds)
    dur = (
        ((str(hours) + ":") if hours else "00:")
        + ((str(minutes) + ":") if minutes else "00:")
        + ((str(seconds)) if seconds else "")
    )
    return dur


def ts(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = (
        ((str(days) + "d, ") if days else "")
        + ((str(hours) + "h, ") if hours else "")
        + ((str(minutes) + "m, ") if minutes else "")
        + ((str(seconds) + "s, ") if seconds else "")
        + ((str(milliseconds) + "ms, ") if milliseconds else "")
    )
    return tmp[:-2]


def hbs(size):
    if not size:
        return ""
    power = 2 ** 10
    raised_to_pow = 0
    dict_power_n = {0: "B", 1: "K", 2: "M", 3: "G", 4: "T", 5: "P"}
    while size > power:
        size /= power
        raised_to_pow += 1
    return str(round(size, 2)) + " " + dict_power_n[raised_to_pow] + "B"


async def progress(current, total, event, start, type_of_ps, file=None):
    now = time.time()
    diff = now - start
    if diff >= 1 and (current == total or diff - getattr(event, "_last_progress_update", 0) >= 2):
        event._last_progress_update = diff
        percentage = current * 100 / total if total else 0
        speed = current / diff if diff else 0
        time_to_completion = round((total - current) / speed) * 1000 if speed else 0
        progress_str = "{0}{1}** {2}%**\n\n".format(
            "".join(["■" for i in range(math.floor(percentage / 10))]),
            "".join(["□" for i in range(10 - math.floor(percentage / 10))]),
            round(percentage, 2),
        )
        tmp = (
            progress_str
            + "**✅ Progress:** {0} \n\n**📁 Total Size:** {1}\n\n**🚀 Speed:** {2}/s\n\n**⏰ Time Left:** {3}\n".format(
                hbs(current),
                hbs(total),
                hbs(speed),
                ts(time_to_completion),
            )
        )
        if file:
            await event.edit(
                "{}\n\nFile Name: {}\n\n{}".format(type_of_ps, file, tmp)
            )
        else:
            await event.edit("{}\n\n{}".format(type_of_ps, tmp))


async def test(event):
    try:
        zylern = "speedtest --simple"
        fetch = await asyncrunapp(
            zylern,
            stdout=asyncPIPE,
            stderr=asyncPIPE,
        )
        stdout, stderr = await fetch.communicate()
        result = str(stdout.decode().strip()) \
            + str(stderr.decode().strip())
        await event.reply("**" + result + "**")
    except FileNotFoundError:
        await event.reply("**Install speedtest-cli**")


async def sysinfo(e):
    if str(e.sender_id) not in OWNER and e.sender_id != DEV:
        return
    total, used, free, disk= disk_usage('/')
    total = hbs(total)
    free = hbs(free)
    memory = virtual_memory()
    mem_p = memory.percent
    mem_t = hbs(memory.total)
    mem_a = hbs(memory.available)
    mem_u = hbs(memory.used)
    await e.reply(f"**OS:** {platform.system()}\n**Version:** {platform.release()}\n**Arch:** {platform.architecture()}\n**Total Disk Space:** {total}\n**Free:** {free}\n**Memory Total:** {mem_t}\n**Memory Free:** {mem_a}\n**Memory Used:** {mem_u}\n")
    return


async def info(file, event):
    process = subprocess.Popen(
        ["mediainfo", file, "--Output=HTML"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    stdout, stderr = process.communicate()
    out = stdout.decode()
    client = TelegraphPoster(use_api=True)
    client.create_api_token("TGVid-Comp-Mediainfo")
    page = client.post(
        title="TGVid-Comp-Mediainfo",
        author=((await event.client.get_me()).first_name),
        author_url=f"https://t.me/{((await event.client.get_me()).username)}",
        text=out,
    )
    return page["url"]


def code(data):
    OK.update({len(OK): data})
    return str(len(OK) - 1)


def decode(key):
    if OK.get(int(key)):
        return OK[int(key)]
    return


async def skip(e):
    wah = e.pattern_match.group(1).decode("UTF-8")
    wh = decode(wah)
    out, dl, id = wh.split(";")
    try:
        if QUEUE.get(int(id)):
            WORKING.clear()
            QUEUE.pop(int(id))
        await e.delete()
        os.system("rm -rf downloads/*")
        os.system("rm -rf encode/*")
        for proc in psutil.process_iter():
            processName = proc.name()
            processID = proc.pid
            print(processName , ' - ', processID)
            if(processName == "ffmpeg"):
             os.kill(processID,signal.SIGKILL)
    except BaseException:
        pass
    return


async def renew(e):
    if str(e.sender_id) not in OWNER and e.sender_id != DEV:
        return
    await e.reply("**Cleared Queued, Working Files and Cached Downloads!**")
    WORKING.clear()
    QUEUE.clear()
    os.system("rm -rf downloads/*")
    os.system("rm -rf encode/*")
    for proc in psutil.process_iter():
        processName = proc.name()
        processID = proc.pid
        print(processName , ' - ', processID)
        if (processName == "ffmpeg"):
         os.kill (processID,signal.SIGKILL)
    return


async def coding(e):
    if str(e.sender_id) not in OWNER and e.sender_id != DEV:
        return
    ffmpeg = e.text.split(" ", maxsplit=1)[1]
    ffmpegcode.clear()
    ffmpegcode.insert(0, f"""{ffmpeg}""")
    await e.reply(f"**Changed FFMPEG Code to**\n\n`{ffmpeg}`")
    return


async def getlogs(e):
    if str(e.sender_id) not in OWNER and e.sender_id != DEV:
        return
    await e.client.send_file(e.chat_id, file=LOG_FILE_NAME, force_document=True)


async def getthumb(e):
    if str(e.sender_id) not in OWNER and e.sender_id != DEV:
        return
    if not THUMBNAIL_PATH.exists():
        return await e.reply("**Thumbnail is not available yet.**")
    await e.client.send_file(e.chat_id, file=str(THUMBNAIL_PATH), force_document=False, caption="**Your Current Thumbnail.**")


async def getcode(e):
    if str(e.sender_id) not in OWNER and e.sender_id != DEV:
        return
    await e.reply(f"**Your Current FFMPEG Code is**\n\n`{ffmpegcode[0]}`")
    return


async def clearqueue(e):
    if str(e.sender_id) not in OWNER and e.sender_id != DEV:
        return
    await e.reply("**Cleared Queued Files!**")
    QUEUE.clear()
    return


async def fast_download(e, download_url, filename=None):
    def progress_callback(d, t):
        return (
            asyncio.get_event_loop().create_task(
                progress(
                    f"**📥 Downloading video from {download_url}**",
                )
            ),
        )

    async with aiohttp.ClientSession() as session:
        async with session.get(download_url, timeout=None) as response:
            if not filename:
                filename = download_url.rpartition("/")[-1]
            filename = unquote(filename)
            filename = os.path.join(str(DOWNLOAD_DIR), filename)
            total_size = int(response.headers.get("content-length", 0)) or None
            downloaded_size = 0
            with open(filename, "wb") as f:
                async for chunk in response.content.iter_chunked(1024):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
            return filename

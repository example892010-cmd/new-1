#    This file is part of the CompressorQueue distribution.
#    Copyright (c) 2021 Danish_00
#    Script Improved by Zylern

import time
from pathlib import Path
from .FastTelethon import download_file, upload_file
from .funcn import *
from .config import *


async def stats(e):
    try:
        wah = e.pattern_match.group(1).decode("UTF-8")
        wh = decode(wah)
        out, dl, id = wh.split(";")
        ot = hbs(int(Path(out).stat().st_size))
        ov = hbs(int(Path(dl).stat().st_size))
        processing_file_name = dl.replace(f"downloads/", "").replace(f"_", " ")
        ans = f"Processing Media:\n{processing_file_name}\n\nDownloaded:\n{ov}\n\nCompressed:\n{ot}"
        await e.answer(ans, cache_time=0, alert=True)
    except Exception as er:
        LOGS.info(er)
        await e.answer(
            "Someting Went Wrong.\nSend Media Again.", cache_time=0, alert=True
        )


async def dl_link(event):
    if not event.is_private:
        return
    if str(event.sender_id) not in OWNER and event.sender_id !=DEV:
        return
    link, name = "", ""
    try:
        link = event.text.split()[1]
        name = event.text.split()[2]
    except BaseException:
        pass
    if not link:
        return
    if WORKING or QUEUE:
        QUEUE.update({link: name})
        return await event.reply(f"**✅ Added {link} in QUEUE**")
    WORKING.append(1)
    s = dt.now()
    xxx = await event.reply("**📥 Downloading...**")
    try:
        dl = await fast_download(xxx, link, name)
    except Exception as er:
        WORKING.clear()
        LOGS.info(er)
        return
    es = dt.now()
    kk = dl.split("/")[-1]
    aa = kk.split(".")[-1]
    newFile = dl.replace(f"downloads/", "").replace(f"_", " ")
    rr = str(ENCODE_DIR)
    bb = kk.replace(f".{aa}", ".mkv")
    out = f"{rr}/{bb}"
    thum = str(THUMBNAIL_PATH)
    dtime = ts(int((es - s).seconds) * 1000)
    hehe = f"{out};{dl};0"
    wah = code(hehe)
    nn = await xxx.edit(
        "**🗜 Compressing...**",
        buttons=[
            [Button.inline("STATS", data=f"stats{wah}")],
            [Button.inline("CANCEL", data=f"skip{wah}")],
        ],
    )
    cmd = f"""ffmpeg -i "{dl}" {ffmpegcode[0]} "{out}" -y"""
    process = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    er = stderr.decode()
    try:
        if er:
            await xxx.edit(str(er) + "\n\n**ERROR**")
            WORKING.clear()
            os.remove(dl)
            return os.remove(out)
    except BaseException:
        pass
    ees = dt.now()
    ttt = time.time()
    await nn.delete()
    nnn = await xxx.client.send_message(xxx.chat_id, "**📤 Uploading...**")
    with open(out, "rb") as f:
        ok = await upload_file(
            client=xxx.client,
            file=f,
            name=out,
            progress_callback=lambda d, t: asyncio.get_event_loop().create_task(
                progress(d, t, nnn, ttt, "**📤 Uploading...**")
            ),
        )
    await nnn.delete()
    org = int(Path(dl).stat().st_size)
    com = int(Path(out).stat().st_size)
    pe = 100 - ((com / org) * 100)
    per = str(f"{pe:.2f}") + "%"
    eees = dt.now()
    x = dtime
    xx = ts(int((ees - es).seconds) * 1000)
    xxxx = ts(int((eees - ees).seconds) * 1000)
    a1 = await info(dl, xxx)
    a2 = await info(out, xxx)
    dk = f"<b>File Name:</b> {newFile}\n\n<b>Original File Size:</b> {hbs(org)}\n<b>Encoded File Size:</b> {hbs(com)}\n<b>Encoded Percentage:</b> {per}\n\n<b>Get Mediainfo Here:</b> <a href='{a1}'>Before</a>/<a href='{a2}'>After</a>\n\n<i>Downloaded in {x}\nEncoded in {xx}\nUploaded in {xxxx}</i>"
    ds = await event.client.send_file(
        event.chat_id, file=ok, caption=dk, force_document=True, link_preview=False, thumb=thum, parse_mode="html"
    )
    os.remove(dl)
    os.remove(out)
    WORKING.clear()


async def _encode_one(event, source, output, height, duration, status_msg):
    """Encode one output height while preserving configured FFmpeg options."""
    import shlex
    args = shlex.split(ffmpegcode[0])
    # Replace the existing fixed-size setting and any existing video filter only;
    # all codec, audio, subtitle, preset and quality settings remain intact.
    cleaned = []
    i = 0
    while i < len(args):
        if args[i] in ("-s", "-vf") and i + 1 < len(args):
            i += 2
            continue
        cleaned.append(args[i])
        i += 1
    cmd = ["ffmpeg", "-y", "-i", source, *cleaned, "-vf", f"scale=-2:{height}",
           "-progress", "pipe:1", "-nostats", output]
    process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE,
                                                   stderr=asyncio.subprocess.PIPE)
    last_update = 0
    while True:
        line = await process.stdout.readline()
        if not line:
            break
        line = line.decode(errors="ignore").strip()
        if line.startswith("out_time_ms=") and duration > 0:
            try:
                elapsed = int(line.split("=", 1)[1]) / 1_000_000
                pct = max(0, min(100, int(elapsed / duration * 100)))
                if pct != last_update and (pct % 5 == 0 or pct == 100):
                    bars = "■" * (pct // 10) + "□" * (10 - pct // 10)
                    await status_msg.edit(f"**🗜 Encoding {height}p**\n{bars} **{pct}%**")
                    last_update = pct
            except Exception:
                pass
    stderr = await process.stderr.read()
    rc = await process.wait()
    if rc != 0:
        raise RuntimeError(stderr.decode(errors="replace")[-3500:] or f"FFmpeg failed ({rc})")


async def _process_video(event, source, original_name, download_seconds=0):
    import subprocess
    from pathlib import Path
    os.makedirs(ENCODE_DIR, exist_ok=True)
    # Probe duration for progress reporting.
    try:
        probe = await asyncio.create_subprocess_exec(
            "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", source,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        p_out, _ = await probe.communicate()
        duration = float(p_out.decode().strip() or 0)
    except Exception:
        duration = 0
    stem = os.path.splitext(os.path.basename(original_name))[0]
    total_encode_start = dt.now()
    for height in (480, 720, 1080):
        out = os.path.join(str(ENCODE_DIR), f"{stem}_{height}p.mkv")
        msg = await event.reply(f"**🗜 Preparing {height}p encoding...**")
        try:
            await _encode_one(event, source, out, height, duration, msg)
        except Exception as exc:
            await msg.edit(f"**❌ Encoding failed ({height}p)**\n`{str(exc)[:3500]}`")
            if os.path.exists(out): os.remove(out)
            continue
        encoded_seconds = (dt.now() - total_encode_start).total_seconds()
        await msg.edit(f"**✅ {height}p encoding complete.**\n**📤 Uploading...**")
        upload_start = time.time()
        try:
            with open(out, "rb") as f:
                uploaded = await upload_file(
                    client=event.client, file=f, name=os.path.basename(out),
                    progress_callback=lambda current, total: asyncio.get_event_loop().create_task(
                        progress(current, total, msg, upload_start, f"**📤 Uploading {height}p**\n__{os.path.basename(out)}__"))
                )
            original_size = os.path.getsize(source)
            output_size = os.path.getsize(out)
            reduction = (1 - output_size / original_size) * 100 if original_size else 0
            caption = (f"**Quality:** {height}p\n**Original Size:** {hbs(original_size)}\n"
                       f"**Encoded Size:** {hbs(output_size)}\n**Size Change:** {reduction:.2f}%")
            await event.client.send_file(event.chat_id, file=uploaded, caption=caption,
                                        force_document=True, link_preview=False,
                                        thumb=str(THUMBNAIL_PATH) if THUMBNAIL_PATH.exists() else None)
            await msg.edit(f"**✅ {height}p completed and uploaded.**")
        except Exception as exc:
            await msg.edit(f"**❌ Upload failed ({height}p)**\n`{str(exc)[:2000]}`")
        finally:
            if os.path.exists(out): os.remove(out)


async def encod(event):
    try:
        if not event.is_private or str(event.sender_id) not in OWNER and event.sender_id != DEV:
            return
        if not event.media or not hasattr(event.media, "document"):
            return
        doc = event.media.document
        if not doc.mime_type.startswith(("video", "application/octet-stream")):
            return
        if WORKING or QUEUE:
            reply = await event.reply("**Adding To Queue...**")
            name = event.file.name or f"video_{dt.now().isoformat('_', 'seconds')}.mp4"
            if doc.id in QUEUE:
                return await reply.edit("**This File is Already Added in Queue**")
            QUEUE[doc.id] = [name, doc, event.chat_id]
            return await reply.edit("**Added This File in Queue**")
        WORKING.append(1)
        status = await event.reply("**📥 Downloading...**")
        started = time.time()
        filename = event.file.name or f"video_{dt.now().isoformat('_', 'seconds')}.mp4"
        dl = os.path.join(str(DOWNLOAD_DIR), filename)
        try:
            with open(dl, "wb") as f:
                await download_file(client=event.client, location=doc, out=f,
                    progress_callback=lambda d, t: asyncio.get_event_loop().create_task(
                        progress(d, t, status, started, f"**📥 Downloading**\n__{filename}__")))
            await _process_video(event, dl, filename, time.time() - started)
        finally:
            if os.path.exists(dl): os.remove(dl)
            WORKING.clear()
    except Exception as er:
        LOGS.exception("Auto encoding failed: %s", er)
        WORKING.clear()

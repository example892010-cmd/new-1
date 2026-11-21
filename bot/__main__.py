#    This file is part of the CompressorQueue distribution.
#    Copyright (c) 2021 Danish_00
#    Script Improved by Zylern


from . import *
from .config import *
from .worker import *
from .devtools import *
from .FastTelethon import *
LOGS.info("Starting...")

try:
    bot.start(bot_token=BOT_TOKEN)
except Exception as er:
    LOGS.info(er)


####### GENERAL CMDS ########

@bot.on(events.NewMessage(pattern="/start"))
async def _(e):
    if str(e.sender_id) not in OWNER and e.sender_id !=DEV:
        return e.reply("**Sorry You're not An Authorised User!**")
    await start(e)


@bot.on(events.NewMessage(pattern="/setcode"))
async def _(e):
    if str(e.sender_id) not in OWNER and e.sender_id !=DEV:
        return e.reply("**Sorry You're not An Authorised User!**")
    await coding(e)


@bot.on(events.NewMessage(pattern="/getcode"))
async def _(e):
    if str(e.sender_id) not in OWNER and e.sender_id !=DEV:
        return e.reply("**Sorry You're not An Authorised User!**")
    await getcode(e)


@bot.on(events.NewMessage(pattern="/showthumb"))
async def _(e):
    if str(e.sender_id) not in OWNER and e.sender_id !=DEV:
        return e.reply("**Sorry You're not An Authorised User!**")
    await getthumb(e)


@bot.on(events.NewMessage(pattern="/logs"))
async def _(e):
    if str(e.sender_id) not in OWNER and e.sender_id !=DEV:
        return e.reply("**Sorry You're not An Authorised User!**")
    await getlogs(e)


@bot.on(events.NewMessage(pattern="/cmds"))
async def _(e):
    if str(e.sender_id) not in OWNER and e.sender_id !=DEV:
        return e.reply("**Sorry You're not An Authorised User!**")
    await zylern(e)


@bot.on(events.NewMessage(pattern="/ping"))
async def _(e):
    if str(e.sender_id) not in OWNER and e.sender_id !=DEV:
        return e.reply("**Sorry You're not An Authorised User!**")
    await up(e)


@bot.on(events.NewMessage(pattern="/sysinfo"))
async def _(e):
    if str(e.sender_id) not in OWNER and e.sender_id !=DEV:
        return e.reply("**Sorry You're not An Authorised User!**")
    await sysinfo(e)


@bot.on(events.NewMessage(pattern="/leech"))
async def _(e):
    if str(e.sender_id) not in OWNER and e.sender_id !=DEV:
        return e.reply("**Sorry You're not An Authorised User!**")
    await dl_link(e)


@bot.on(events.NewMessage(pattern="/help"))
async def _(e):
    if str(e.sender_id) not in OWNER and e.sender_id !=DEV:
        return e.reply("**Sorry You're not An Authorised User!**")
    await ihelp(e)


@bot.on(events.NewMessage(pattern="/renew"))
async def _(e):
    if str(e.sender_id) not in OWNER and e.sender_id !=DEV:
        return e.reply("**Sorry You're not An Authorised User!**")
    await renew(e)


@bot.on(events.NewMessage(pattern="/clear"))
async def _(e):
    if str(e.sender_id) not in OWNER and e.sender_id !=DEV:
        return e.reply("**Sorry You're not An Authorised User!**")
    await clearqueue(e)


@bot.on(events.NewMessage(pattern="/speed"))
async def _(e):
    if str(e.sender_id) not in OWNER and e.sender_id !=DEV:
        return e.reply("**Sorry You're not An Authorised User!**")
    await test(e)
    
    

########## Direct ###########

@bot.on(events.NewMessage(pattern="/eval"))
async def _(e):
    await eval(e)

@bot.on(events.NewMessage(pattern="/bash"))
async def _(e):
    await bash(e)


######## Callbacks #########

@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"stats(.*)")))
async def _(e):
    await stats(e)

@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"skip(.*)")))
async def _(e):
    await skip(e)

@bot.on(events.callbackquery.CallbackQuery(data=re.compile("help")))
async def _(e):
    await help(e)

########## AUTO ###########

@bot.on(events.NewMessage(incoming=True))
async def _(event):
        if str(event.sender_id) not in OWNER and event.sender_id !=DEV:
            return await event.reply_text("**Sorry You're not An Authorised User!**")
        if not event.photo:
            return
        os.system("rm thumb.jpg")
        await event.client.download_media(event.media, file="/bot/thumb.jpg")
        await event.reply("**Thumbnail Saved Successfully.**")


@bot.on(events.NewMessage(incoming=True))
async def _(e):
    await encod(e)


async def something():
    while True:
        try:
            if not WORKING and QUEUE:
                key = next(iter(QUEUE))
                item = QUEUE[key]
                WORKING.append(1)
                if isinstance(item, str):
                    name = item or "downloaded_video.mkv"
                    chat_id = int(OWNER.split()[0])
                    status = await bot.send_message(chat_id, f"**📥 Downloading queued link**\n__{name}__")
                else:
                    name, document, chat_id = item
                    status = await bot.send_message(chat_id, f"**📥 Downloading queued file**\n__{name}__")
                started = time.time()
                dl = os.path.join("downloads", name)
                try:
                    if isinstance(item, str):
                        dl = await fast_download(status, key, name)
                    else:
                        with open(dl, "wb") as f:
                            await download_file(client=bot, location=document, out=f,
                                progress_callback=lambda d, t: asyncio.get_event_loop().create_task(
                                    progress(d, t, status, started, f"**📥 Downloading**\n__{name}__")))
                    await _process_video(status, dl, name, time.time() - started)
                except Exception as exc:
                    LOGS.exception("Queued job failed: %s", exc)
                    await status.edit(f"**❌ Queue job failed**\n`{str(exc)[:3000]}`")
                finally:
                    if os.path.exists(dl): os.remove(dl)
                    QUEUE.pop(key, None)
                    WORKING.clear()
            else:
                await asyncio.sleep(3)
        except Exception as err:
            LOGS.exception("Queue worker error: %s", err)
            WORKING.clear()
            await asyncio.sleep(3)


########### Start ############

LOGS.info("Bot has started.")
with bot:
    bot.loop.run_until_complete(something())
    bot.loop.run_forever()
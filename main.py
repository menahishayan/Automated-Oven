#!/usr/bin/python3

import asyncio
import EventHandler
import time
start = time.process_time()

__version__ = '0.20.3'

async def startLoop():
    e = EventHandler.EventHandler()
    e.log("Boot: v"+ __version__)
    await e.init()
    e.log("Boot: {} s".format(round(time.process_time()-start,1)))
    await e.dispatch([
        [e.startDetectionLoop],
        [e.server.serveforever],
        # [e.display.cookingListener],
        [e.energy.logEnergy]
    ])

asyncio.run(startLoop())

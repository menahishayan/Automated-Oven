#!/usr/bin/python3

import asyncio
import EventHandler
import time
start = time.process_time()

__version__ = '0.17.2'

async def startLoop():
    e = EventHandler.EventHandler()
    e.log("Version: "+ __version__)
    await e.init()
    e.log("StartUpTime: " + str(time.process_time()-start))
    await e.dispatch([
        [e.startDetectionLoop],
        [e.server.serveforever],
        [e.display.cookingListener],
        [e.energy.logEnergy]
    ])

asyncio.run(startLoop())

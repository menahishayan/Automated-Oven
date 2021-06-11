#!/usr/bin/python3

import asyncio
import EventHandler
import time
start = time.process_time()

async def startLoop():
    e = EventHandler.EventHandler()
    await e.init()
    e.log("Boot: {} s".format(round(time.process_time()-start,1)))
    await e.dispatch([
        [e.startDetectionLoop],
        [e.server.serveforever],
        [e.cook.cookingHandler],
        [e.energy.logEnergy]
    ])

asyncio.run(startLoop())

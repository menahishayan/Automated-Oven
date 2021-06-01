#!/usr/bin/python3

import asyncio
import EventHandler
import time
start = time.time()

__version__ = '0.11.0'


async def startLoop():
    e = EventHandler.EventHandler()
    e.log(__version__)
    await e.init()
    e.log(time.time()-start)
    await e.dispatch([
        [e.startDetectionLoop],
        [e.server.serveforever],
        [e.display.cookingListener],
        [e.energy.logEnergy]
    ])


if __name__ == '__main__':
    asyncio.run(startLoop())

#!/usr/bin/python3

import time
start = time.time()
import EventHandler
import asyncio

__version__ = '0.9.0'

async def startLoop():
    e = EventHandler.EventHandler()
    e.log(__version__)
    await e.init()
    e.log(time.time()-start)
    await e.dispatch([[e.startDetectionLoop],[e.server.serveforever],[e.display.cookingListener]])


if __name__ == '__main__':
    asyncio.run(startLoop())

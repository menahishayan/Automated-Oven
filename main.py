import time
start = time.process_time()
import EventHandler
import asyncio

__version__ = '0.8.3'

async def startLoop():
    e = EventHandler.EventHandler()
    e.log(__version__)
    await e.init()
    e.log(time.process_time()-start)
    await e.dispatch([[e.startDetectionLoop],[e.server.serveforever],[e.display.cookingListener]])


if __name__ == '__main__':
    asyncio.run(startLoop())

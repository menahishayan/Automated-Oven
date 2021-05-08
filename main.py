import time
start = time.process_time()
import EventHandler
import asyncio

__version__ = '0.7.0'

async def startLoop():
    e = EventHandler.EventHandler()
    e.log(__version__)
    await e.init()
    e.log(time.process_time()-start)
    await e.startDetectionLoop()


if __name__ == '__main__':
    asyncio.run(startLoop())

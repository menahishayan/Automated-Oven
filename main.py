import time
start = time.process_time()
import EventHandler
import asyncio

__version__ = '0.6.0'

async def startLoop():
    e = EventHandler.EventHandler()
    e.log(__version__)
    await e.init()
    e.log(time.process_time()-start)
    await e.startDetectionLoop()
    # cook = Cook.Cook(logging)
    # wm = pyinotify.WatchManager()
    # mask = pyinotify.IN_MODIFY
    
    # handler = EventHandler('logfile.log')
    # notifier = pyinotify.Notifier(wm, handler)

    # wm.add_watch(handler.file_path, mask)        
    # notifier.loop()
    
    

if __name__ == '__main__':
    asyncio.run(startLoop())

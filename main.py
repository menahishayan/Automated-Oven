import time

# from numpy.lib.function_base import disp
start = time.process_time()

from sys import stdout
import concurrent.futures as cf
import logging
import asyncio
import DetectItem
import DisplayContent
# import pyinotify
# import re
# from os import path

__version__ = '0.5.0'

logger_format = '%(asctime)s:%(funcName)s:%(message)s'
logging.basicConfig(format=logger_format, level=logging.INFO, datefmt="%H:%M:%S", filename='./logfile.log', filemode='w')
logging.getLogger().addHandler(logging.StreamHandler(stdout))

display = DisplayContent.DisplayContent()

# class EventHandler (pyinotify.ProcessEvent):
#     def __init__(self, file_path, *args, **kwargs):
#         super(EventHandler, self).__init__(*args, **kwargs)
#         self.file_path = file_path
#         self._last_position = 0
#         logpats = r'detectionDispatcher'
#         self._logpat = re.compile(logpats)

#     def process_IN_MODIFY(self, event):
#         # print("File changed: ", event.pathname)
#         if self._last_position > path.getsize(self.file_path):
#             self._last_position = 0
#         with open(self.file_path) as f:
#             f.seek(self._last_position)
#             loglines = f.readlines()
#             self._last_position = f.tell()
#             groups = (self._logpat.search(line.strip()) for line in loglines)
#             for g in groups:
#                 if g:
#                     print(g.string)

async def detectorLoadProgress(detector):
    loopStart = time.process_time()
    
    while time.process_time() - loopStart <= 178:
        await asyncio.sleep(1.78)
        s = await detector.success()
        if s == True:
            return

        percent = int((time.process_time()*100)/178)-1
        display.circleProgress(percent, "{}%".format(percent))
        if percent % 10 == 0:
            logging.info(str(percent))

        if percent % 20 == 0:
            stat = await detector.get_status()
            logging.info(stat)

def genericThreadWorker(fn,arg=None):
    if arg:
        asyncio.run(fn(arg))
    else: 
        asyncio.run(fn())

def progressWorker(detector):
    asyncio.run(detectorLoadProgress(detector))

def detectionWorker(detector):
    # Trigger ultrasound motion
    logging.info("Awaiting User Input")
    display.text("Place The Item")

    while input() == 'd':
        display.loading()
        detectedItem = asyncio.run(detector.captureFrames())
        print(detectedItem)
        display.text(detectedItem)

async def startLoop():
    logging.info('Start')
    logging.info(__version__)

    detector = DetectItem.Detector()

    # wm = pyinotify.WatchManager()
    # mask = pyinotify.IN_MODIFY
    
    # handler = EventHandler('logfile.log')
    # notifier = pyinotify.Notifier(wm, handler)

    # wm.add_watch(handler.file_path, mask)        
    # notifier.loop()
    

    arrayOfFutures = []
    with cf.ThreadPoolExecutor(max_workers=2) as executor:
        loop = asyncio.get_running_loop()
        arrayOfFutures.append(loop.run_in_executor(executor, genericThreadWorker, detector.init, logging))
        arrayOfFutures.append(loop.run_in_executor(executor, progressWorker, detector))
        arrayOfFutures.append(loop.run_in_executor(executor, genericThreadWorker, detector.load_model))

        await asyncio.gather(*arrayOfFutures)

        # arrayOfFutures.append(loop.run_in_executor(executor, genericThreadWorker, notifier.loop))
        arrayOfFutures.append(loop.run_in_executor(executor, detectionWorker, detector))
        await asyncio.gather(arrayOfFutures[-1])
    

if __name__ == '__main__':
    asyncio.run(startLoop())

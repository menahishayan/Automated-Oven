import logging
from logging.handlers import SysLogHandler
import concurrent.futures as cf
import asyncio

from DetectItem import Detector
from DisplayContent import DisplayContent
from Cook import Cook
from Ultrasound import Ultrasound
from Temp import Temp
from SimpleWebSocketServer import SimpleWebSocketServer
import WebSocketServer
from Energy import Energy
from DB import DB
from Automations import Automations
from Audio import Audio

import signal

class EventHandler:
    def __init__(self):
        self.__version__ = '1.5.0'

        logger_format = '%(asctime)s %(message)s'
        logging.basicConfig(format=logger_format, level=logging.INFO,
                            datefmt="%H:%M:%S", filename='./logfile.log', filemode='w')
        logging.getLogger().addHandler(SysLogHandler(facility=SysLogHandler.LOG_DAEMON, address='/dev/log'))

        # logging.info('Start')
        self._SIGKILL = False

        self.logging = logging

        self.config = DB('./config.json')

        self.display = DisplayContent()
        self.detector = Detector()
        self.ultrasound = Ultrasound()
        self.temp = Temp()
        self.server = SimpleWebSocketServer('', 8069, WebSocketServer.WebSocketServer,self)
        self.cook = Cook(self)
        self.energy = Energy(self)
        self.history = DB('./HistoryDB.json')
        self.audio = Audio(self)
        self.automations = Automations()

        signal.signal(signal.SIGTERM, self.sig_handler)
        signal.signal(signal.SIGINT, self.sig_handler)

        self.log("Boot: v"+ self.__version__)

        # signal.signal(signal.SIGSTOP, self.sig_handler)

    def log(self, msg):
        self.logging.info(msg)

    def err(self, msg):
        self.logging.error(msg)

    def sig_handler(self,signum, stack):
        self._SIGKILL = True
        self.server.close()
        exit()

    def dispatchWorker(self, fn, *args):
        return asyncio.run(fn(*args))

    async def startDetectionLoop(self):
        await self.dispatch([
            # [self.display.text, "Place The Item"],
            [self.cook.init]
        ])

        try:
            while not self._SIGKILL:
                await self.temp.update()
                if not self.cook.isCooking:
                    dist = await self.ultrasound.get()
                    self.log(dist)
                    if dist < 16:
                        tasks = await self.dispatch([
                            [self.display.loading],
                            [self.detector.detect],
                        ])

                        res = tasks[1].result()

                        self.log("Detection: " + res)

                        await self.cook.startFromDB(res)
                    else:
                        await asyncio.sleep(0.3)
                else:
                    await asyncio.sleep(1)
        except Exception as e:
            self.err(e)


    async def dispatch(self, arrayOfDispatches):
        arrayOfFutures = []
        with cf.ThreadPoolExecutor(max_workers=4) as executor:
            loop = asyncio.get_running_loop()
            for d in arrayOfDispatches:
                arrayOfFutures.append(loop.run_in_executor(
                    executor, self.dispatchWorker, *d))
            await asyncio.gather(*arrayOfFutures)

            return arrayOfFutures

    async def init(self):
        await self.dispatch([
            [self.display.init, self]
        ])
        await self.dispatch([
            [self.display.loading],
            [self.detector.init, self],
            [self.detector.load_model]
        ])


import logging
from logging.handlers import SysLogHandler
import concurrent.futures as cf
from sys import stdout
import asyncio
import DetectItem
import DisplayContent
import Cook
import Ultrasound
import Temp
from SimpleWebSocketServer import SimpleWebSocketServer
import Energy
import DB
import Automations
import Audio
import signal
from os import kill, getpid

class EventHandler:
    def __init__(self):
        logger_format = '%(asctime)s %(message)s'
        logging.basicConfig(format=logger_format, level=logging.INFO,
                            datefmt="%H:%M:%S", filename='./logfile.log', filemode='w')
        logging.getLogger().addHandler(SysLogHandler(facility=SysLogHandler.LOG_DAEMON, address='/dev/log'))

        # logging.info('Start')
        self._SIGKILL = False

        self.logging = logging
        self.display = DisplayContent.DisplayContent()
        self.detector = DetectItem.Detector()
        self.ultrasound = Ultrasound.Ultrasound()
        self.temp = Temp.Temp()
        self.server = SimpleWebSocketServer('', 8069, WebSocketServer.WebSocketServer,self)
        self.cook = Cook.Cook(self)
        self.energy = Energy.Energy(self)
        self.history = DB.DB('./HistoryDB.json')
        self.audio = Audio.Audio()
        self.automations = Automations.Automations()
        signal.signal(signal.SIGTERM, self.sig_handler)
        signal.signal(signal.SIGINT, self.sig_handler)
        # signal.signal(signal.SIGSTOP, self.sig_handler)

    def log(self, msg):
        self.logging.info(msg)

    def err(self, msg):
        self.logging.error(msg)

    def sig_handler(self,signum, stack):
        self._SIGKILL = True
        self.log("Event: Recieved " + str(signal.Signals(signum).name))
        self.server.close()
        exit()

    def poweroff(self):
        kill(getpid(), signal.SIGTERM)

    def dispatchWorker(self, fn, *args):
        return asyncio.run(fn(*args))

    async def startDetectionLoop(self):
        await self.dispatch([
            [self.display.text, "Place The Item"],
            [self.cook.init]
        ])

        while not self._SIGKILL:
            await self.temp.update()
            if not self.cook.isCooking:
                dist = await self.ultrasound.get()

                if dist < 16:
                    tasks = await self.dispatch([
                        [self.display.loading],
                        [self.detector.detect],
                    ])

                    res = tasks[1].result()

                    self.log("Detection: " + res)

                    await self.dispatch([
                        [self.cook.start, res]
                    ])
                else:
                    await asyncio.sleep(0.3)
            else:
                await asyncio.sleep(1)


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


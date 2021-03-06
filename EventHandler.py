import logging
from logging.handlers import SysLogHandler
import concurrent.futures as cf
import asyncio
from sys import exc_info
from os import system
import signal
from json import load

from DetectItem import Detector
from DisplayContent import DisplayContent
from Cook import Cook
from Ultrasound import Ultrasound
from Temp import Temp
from SimpleWebSocketServer import SimpleWebSocketServer
from WebSocketServer import WebSocketServer
from Energy import Energy
from DB import DB
from Audio import Audio
from Users import Users
from History import History
from Automations import Automations
from Network import Network

class EventHandler:
    def __init__(self):
        self.__version__ = '3.1.3'

        logger_format = '%(asctime)s %(message)s'
        logging.basicConfig(format=logger_format, level=logging.INFO,
                            datefmt="%H:%M:%S", filename='./logfile.log', filemode='w')
        logging.getLogger().addHandler(SysLogHandler(facility=SysLogHandler.LOG_DAEMON, address='/dev/log'))

        self._SIGKILL = False
        self.logging = logging
        self.config = DB('./config.json')

        self.network = Network(self)
        self.display = DisplayContent()
        self.detector = Detector()
        self.ultrasound = Ultrasound(self)
        self.temp = Temp()
        self.server = SimpleWebSocketServer('', 8069, WebSocketServer, self)
        self.cook = Cook(self)
        self.energy = Energy(self)
        self.history = History(self)
        self.audio = Audio(self)
        self.users = Users(self)
        self.automations = Automations(self)

        signal.signal(signal.SIGTERM, self.sig_handler)
        signal.signal(signal.SIGINT, self.sig_handler)

        self.log("Boot: v" + self.__version__)

    def log(self, msg):
        self.logging.info(msg)

    def err(self, msg):
        self.logging.error(msg)
        self.logging.error(exc_info()[-1].tb_lineno)

    def sig_handler(self, _, _2):
        self._SIGKILL = True
        self.server.close()
        exit()

    def poweroff(self):
        system('sudo shutdown -h now')

    async def startWebsocket(self):
        while not self._SIGKILL:
            self.server.serveonce()

    def dispatchWorker(self, fn, *args):
        return asyncio.run(fn(*args))

    async def startDetectionLoop(self):
        try:
            while not self._SIGKILL:
                networkStatus = await self.network.get()
                if networkStatus == 'connected':
                    break
                self.display.network("Automated Oven" if networkStatus == 'hostapd' else "Connecting")
                await asyncio.sleep(0.5)

            self.log("Network: Connected")

            await self.dispatch([
                [self.display.text, "Place The Item"],
                [self.cook.init]
            ])
        
            while not self._SIGKILL:
                await self.temp.update()
                if not self.cook.isCooking and await self.config.get('autoDetect'):
                    dist = await self.ultrasound.get()
                    if dist < await self.config.get('sensitivity')*0.17:
                        tasks = await self.dispatch([
                            [self.display.loading],
                            [self.detector.detect],
                        ])

                        res = tasks[1].result()

                        self.log("Detection: " + res)

                        await self.cook.startFromDB(res)
                    else:
                        await asyncio.sleep(await self.config.get('responsiveness')*0.003)
                else:
                    await asyncio.sleep(await self.config.get('responsiveness')*0.01)
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
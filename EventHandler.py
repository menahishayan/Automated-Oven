import logging
import concurrent.futures as cf
from sys import stdout
import asyncio
import DetectItem
import DisplayContent
import Cook
from SimpleWebSocketServer import SimpleWebSocketServer
import WebSocketServer
import Energy
import History
from os import kill, getpid
from signal import SIGINT

class EventHandler:
    def __init__(self):
        logger_format = '%(asctime)s %(message)s'
        logging.basicConfig(format=logger_format, level=logging.INFO,
                            datefmt="%H:%M:%S", filename='./logfile.log', filemode='w')
        # logging.getLogger().addHandler(logging.StreamHandler(stdout))

        logging.info('Start')

        self.logging = logging
        self.display = DisplayContent.DisplayContent()
        self.detector = DetectItem.Detector()
        self.server = SimpleWebSocketServer('', 8069, WebSocketServer.WebSocketServer,self)
        self.cook = Cook.Cook(self)
        self.energy = Energy.Energy()
        self.history = History.History()

    def log(self, msg):
        self.logging.info(msg)

    def err(self, msg):
        self.logging.error(msg)

    def dispatchWorker(self, fn, *args):
        return asyncio.run(fn(*args))

    async def startDetectionLoop(self):
        await self.dispatch([
            [self.display.text, "Place The Item"],
            [self.cook.init]
        ])

        while input("Proceed? (y/n) ") == 'y':
            tasks = await self.dispatch([
                [self.display.loading],
                [self.detector.detect],
            ])

            res = tasks[1].result()

            self.log(res)

            await self.dispatch([
                [self.cook.start, res]
            ])
        self.server.close()
        kill(getpid(), SIGINT)
        exit()


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


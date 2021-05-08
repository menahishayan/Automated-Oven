from pandas import read_csv
import time
import asyncio
__version__ = '0.6.0'

class Cook:
    def __init__(self,e):
        self.e = e
        self.item,self.top,self.bottom,self.endTime,self.cooktype = '',180,180,20,'Cook'
        self.isPaused = False
        self.isCooking = False

    async def init(self, method='fixed'):
        if method=='fixed':
            self.df = read_csv('Temp.csv', index_col=0)
        # derived 

    async def start(self, item):
        # steps
        try:
            self.top = self.df['Top'][item]
            self.bottom = self.df['Bottom'][item]
            self.endTime = time.process_time() + self.df['Time'][item] # * 60
            self.cooktype = self.df['Type'][item]

            self.startTime = time.process_time()

            self.item = item

        except Exception as e:
            self.e.err("Cook - Unknown Food")
            self.e.err(e)

        self.isCooking = True

        await self.e.dispatch([
            [self.e.display.cooking, self.item,self.top,self.bottom,self.startTime,self.endTime,self.cooktype]
        ])

    async def pause(self):
        await asyncio.sleep(5)
        self.pauseTime = time.process_time()
        self.isPaused = True

        self.e.log("Paused - " + str(int(self.pauseTime - self.startTime)))

        # await self.e.dispatch([
        #     [self.e.display.text, "{}\nPaused".format(self.item)]
        # ])
            # self.rods.setTop(top)
            # self.rods.setBottom(bottom)

    async def get(self):
        return {
            'top': self.top,
            'bottom': self.bottom,
            'startTime': self.startTime or None,
            'endTime': self.endTime,
            'cooktype': self.cooktype,
            'isPaused': self.isPaused,
            'isCooking': self.isCooking,
            'pauseTime': self.pauseTime or None
        }

        
        

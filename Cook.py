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
        self.startTime, self.pauseTime = None,None

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

    def get(self):
        try:
            if self.isCooking == True:
                if self.isPaused == False:
                    return {
                        'top': self.top,
                        'bottom': self.bottom,
                        'startTime': time.process_time() - self.startTime,
                        'endTime': self.endTime - time.process_time(),
                        'cooktype': self.cooktype,
                        'isPaused': self.isPaused,
                        'isCooking': self.isCooking,
                        'pauseTime': 0,
                    }
                else:
                    return {
                        'top': self.top,
                        'bottom': self.bottom,
                        'startTime': time.process_time() - self.startTime,
                        'endTime': self.endTime - time.process_time(),
                        'cooktype': self.cooktype,
                        'isPaused': self.isPaused,
                        'isCooking': self.isCooking,
                        'pauseTime': time.process_time() - self.pauseTime,
                    }
            else:
                return {
                        'top': self.top,
                        'bottom': self.bottom,
                        'startTime': 0,
                        'endTime': 0,
                        'cooktype': self.cooktype,
                        'isPaused': self.isPaused,
                        'isCooking': self.isCooking,
                    }
        except Exception as e:
            self.e.log(e)
            return {
                'error': str(e)
            }

        
        

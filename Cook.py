from pandas import read_csv
import time
import asyncio
__version__ = '0.6.0'


class Cook:
    def __init__(self, e):
        self.e = e
        self.item, self.top, self.bottom, self.endTime, self.cooktype = '', 180, 180, 0, 'Cook'
        self.isPaused = False
        self.isCooking = False
        self.startTime, self.pauseTime = None, None

    async def init(self, method='fixed'):
        if method == 'fixed':
            self.df = read_csv('Temp.csv', index_col=0)
        # derived

    async def start(self, item):
        # steps
        try:
            self.top = int(self.df['Top'][item])
            self.bottom = int(self.df['Bottom'][item])
            self.endTime = time.time() + (int(self.df['Time'][item])  * 60)
            self.cooktype = str(self.df['Type'][item])
            self.startTime = time.time()

            self.item = item

        except Exception as e:
            self.e.err("Cook - Unknown Food")
            self.e.err(e)
            self.item, self.top, self.bottom, self.endTime, self.cooktype = '', 180, 180, 20 + time.time(), 'Cook'


        self.isCooking = True

    async def pause(self):
        try:
            self.pauseTime = time.time()
            self.isPaused = True

            self.e.log("Paused")
            return True
        except:
            return False
        # await self.e.dispatch([
        #     [self.e.display.text, "{}\nPaused".format(self.item)]
        # ])
            # self.rods.setTop(top)
            # self.rods.setBottom(bottom)

    async def resume(self):
                # steps
        try:
            self.startTime = time.time() -(self.pauseTime-self.startTime)
            self.endTime = self.endTime + (time.time()-self.pauseTime)

            self.isPaused = False

            self.e.log("Resumed")

            return True
        except Exception as e:
            self.e.err(e)
            return False

    def get(self):
        try:
            if self.isCooking == True:
                if self.isPaused == False:
                    return {
                        'item': self.item,
                        'top': self.top,
                        'bottom': self.bottom,
                        'startTime': self.startTime,
                        'endTime': self.endTime,
                        'cooktype': self.cooktype,
                        'isPaused': self.isPaused,
                        'isCooking': self.isCooking,
                        'pauseTime': 0,
                    }
                else:
                    return {
                        'item': self.item,
                        'top': self.top,
                        'bottom': self.bottom,
                        'startTime': self.startTime,
                        'endTime': self.endTime,
                        'cooktype': self.cooktype,
                        'isPaused': self.isPaused,
                        'isCooking': self.isCooking,
                        'pauseTime': self.pauseTime,
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

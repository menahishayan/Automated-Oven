from pandas import read_csv
import time
import RodControl
from board import D12

class Cook:
    def __init__(self, e):
        self.e = e
        self.item, self.top, self.bottom, self.endTime, self.cooktype = '', 0, 0, 0, 'Cook'
        self.isPaused = False
        self.isCooking = False
        self.startTime, self.pauseTime = None, None
        self.topRod = RodControl.RodControl(D12,e)

    async def init(self, method='fixed'):
        if method == 'fixed':
            self.df = read_csv('Temp.csv', index_col=0)
        # derived

    async def start(self, item):
        # steps
        try:
            self.top = int(self.df['Top'][item])
            self.bottom = int(self.df['Bottom'][item])
            self.endTime = time.time() + (int(self.df['Time'][item])  * 10)
            self.cooktype = str(self.df['Type'][item])
            self.startTime = time.time()

            self.item = item

            await self.e.dispatch([[self.topRod.setTemp,self.top]])

        except Exception as e:
            self.e.err("Cook - Unknown Food")
            self.e.err(e)
            self.item, self.top, self.bottom, self.endTime, self.cooktype = '', 180, 180, 20 + time.time(), 'Cook'

        self.isCooking = True

    async def pause(self):
        try:
            self.pauseTime = time.time()
            self.isPaused = True

            self.e.log("CookingHandler: Paused")
            return True
        except:
            return False
    
        # self.rods.setBottom(bottom)

    async def resume(self):
                # steps
        try:
            self.startTime = time.time() -(self.pauseTime-self.startTime)
            self.endTime = self.endTime + (time.time()-self.pauseTime)

            self.isPaused = False

            self.e.log("CookingHandler: Resumed")

            return True
        except Exception as e:
            self.e.err(e)
            return False

    async def stop(self):
                # steps
        try:
            self.startTime = 0
            self.endTime = 0
            self.isPaused = False
            self.isCooking = False

            self.e.log("CookingHandler: Stopped")

            return True
        except Exception as e:
            self.e.err(e)
            return False

    async def setTopTemp(self, temp):
                # steps
        try:
            self.top = int(temp)
            self.topRod.set(self.top)
            return True
        except Exception as e:
            self.e.err(e)
            return False

    async def setBottomTemp(self, temp):
                # steps
        try:
            self.bottom = int(temp)
            return True
        except Exception as e:
            self.e.err(e)
            return False

    async def setTime(self, t):
                # steps
        try:
            if self.startTime > 0 and self.isCooking == True:
                self.endTime = self.startTime + int(t)
                return True
            else:
                raise Exception("Cook.setTime is only supported during cooking")
        except Exception as e:
            self.e.err(e)
            return False

    async def get(self):
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

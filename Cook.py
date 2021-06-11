import asyncio
from asyncio.tasks import sleep
from pandas import read_csv
from time import time
import RodControl
from board import D12
from DB import DB

class Cook:
    def __init__(self, e):
        self.e = e
        self.item, self.top, self.bottom, self.endTime, self.cooktype = '', 0, 0, 0, 'Cook'
        self.SIGPAUSE = False
        self.isCooking = False
        self.startTime, self.pauseTime = None, None
        self.topRod = RodControl.RodControl(D12,e)

        self.steps = None
        self.currentStep = -1
        self.totalSteps = 0

    async def init(self, method='fixed'):
        # if method == 'fixed':
        self.df = read_csv('Temp.csv', index_col=0)
        self.db = DB('./FoodDB.json')
        # derived

    async def start(self, item):
        # steps
        try:
            self.top = int(self.df['Top'][item])
            self.bottom = int(self.df['Bottom'][item])
            self.endTime = time() + (int(self.df['Time'][item])  * 20)
            self.cooktype = str(self.df['Type'][item])
            self.startTime = time()

            self.item = item

            self.isCooking = True

            self.steps = self.db._get(item).copy()['steps']
            self.totalSteps = len(self.steps)

            for s in range(self.totalSteps):
                self.currentStep = s
                step = self.steps[s]

                step['isDone'] = False

                while not step['isDone'] and not self.e._SIGKILL:
                    await getattr(self,step['type'])(self.steps[self.currentStep])
                    while self.SIGPAUSE and not self.e._SIGKILL:
                        await sleep(1)

            self.done()

        except Exception as e:
            self.e.err(e)
            self.item, self.top, self.bottom, self.endTime, self.cooktype = '', 180, 180, 20 + time(), 'Cook'

    async def sleepTill(self,end):
        while time() <= end and not self.e._SIGKILL:
            await sleep(1)

    async def preheat(self,s):
        s['startTime'] = time()
        self.e.log("Cooking: Preheating")

        heatTime = self.topRod.heatingTime(s['temp'])
        end = s['startTime'] + (heatTime if heatTime >=0 else self.topRod.coolingTime(s['temp']))

        s['endTime'] = end

        await self.topRod.reachTemp(s['temp'])

        if time() > end:
            s['isDone'] = True
            
        return

    async def cook(self,s):
        duration = s['duration']*10 # *60
        self.e.log("Cooking: Cooking {}".format(duration))
        

        if 'pauseTime' not in s:
            s['startTime'] = time()
            s['endTime'] = s['startTime'] + duration 
        else:
            # s['startTime'] = time() -(s['pauseTime']-s['startTime'])
            # s['endTime'] = s['endTime'] + (time()-s['pauseTime'])

            self.e.log("Start: {}".format(time() - s['startTime']))
            self.e.log("End: {}".format(s['endTime'] - time()))
            # end = s['endTime']

            del(s['pauseTime'])

        await self.topRod.sustainTemp(s['topTemp'],s['endTime'])

        if time() > s['endTime']:
            s['isDone'] = True
        self.e.log("{} Done: {}".format(s['type'],s['isDone']))
            
        return

    async def checkpoint(self,s):
        
        s['startTime'] = time()
        self.e.log("Cooking: Checkpoint")

        end = s['startTime'] + s['maxWaitTime']

        s['endTime'] = end

        await self.sleepTill(end)

        # if time() >= end:
        s['isDone'] = True
            
        return

    async def notify(self,s):
        
        self.e.log("Cooking: Notify")

        s['isDone'] = True
            
        return

    async def cool(self,s):
        
        s['startTime'] = time()
        self.e.log("Cooking: Cool")

        self.topRod.off()

        end = s['startTime'] + s['duration'] # *10

        s['endTime'] = end

        await self.sleepTill(end)

        # if time() >= end:
        s['isDone'] = True
            
        return

    async def pause(self,s=None):
        if self.SIGPAUSE:
            return True
        try:
            self.e.log("Cooking: Paused")
            self.steps[self.currentStep]['pauseTime'] = time()
            # self.pauseTime = time() # legacy
            self.SIGPAUSE = True

            self.topRod.off()

            return True
        except:
            return False
    
    async def resume(self):
        if not self.SIGPAUSE:
            return True
        try:
            s = self.steps[self.currentStep]
            s['startTime'] = time() -(s['pauseTime']-s['startTime'])
            s['endTime'] = s['endTime'] + (time()-s['pauseTime'])

            self.e.log("Start_R: {}".format(time() - self.steps[self.currentStep]['startTime']))
            self.e.log("End_R: {}".format(s['endTime'] - time()))

            self.SIGPAUSE = False

            self.e.log("Cooking: Resumed")

            return True
        except Exception as e:
            self.e.err(e)
            return False

    def done(self):
        self.isCooking = False
        self.cooktype = 'Done'
        self.topRod.off()

        self.steps = None
        self.currentStep = -1
        self.totalSteps = 0

    async def stop(self):
                # steps
        try:
            self.topRod.off()
            self.SIGPAUSE = False
            self.isCooking = False

            self.e.log("Cooking: Stopped")

            return True
        except Exception as e:
            self.e.err(e)
            return False

    async def setTopTemp(self, temp):
                # steps
        try:
            self.top = int(temp)
            await self.e.dispatch([[self.topRod.reachTemp,self.top]])
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
                if self.SIGPAUSE == False:
                    return {
                        'item': self.item,
                        
                        'steps': self.steps,
                        'currentStep': self.currentStep,

                        'cooktype': self.cooktype,
                        'isPaused': self.SIGPAUSE,
                        'isCooking': self.isCooking,
                        'pauseTime': 0,
                    }
                else:
                    return {
                        'item': self.item,

                        'steps': self.steps,
                        'currentStep': self.currentStep,

                        'cooktype': self.cooktype,
                        'isPaused': self.SIGPAUSE,
                        'isCooking': self.isCooking,
                        'pauseTime': self.pauseTime,
                    }
            else:
                return {
                    'steps': self.steps,
                    'currentStep': self.currentStep,

                    'cooktype': self.cooktype,
                    'isPaused': self.SIGPAUSE,
                    'isCooking': self.isCooking,
                }
        except Exception as e:
            self.e.log(e)
            return {
                'error': str(e)
            }

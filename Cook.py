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
        self.isPaused = False
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

            # await self.topRod.set(self.top)

            self.steps = (await self.db.get(item))['steps']
            self.totalSteps = len(self.steps)

            for s in range(self.totalSteps):
                self.currentStep = s
                step = self.steps[s]
                await getattr(self,step['type'])(step if len(step) > 1 else None)
            self.done()

        except Exception as e:
            self.e.err(e)
            self.item, self.top, self.bottom, self.endTime, self.cooktype = '', 180, 180, 20 + time(), 'Cook'

    async def sleepTill(self,end):
        while time() <= end and not self.e._SIGKILL:
            await sleep(1)

    async def preheat(self,args):
        self.e.log("Cooking: Preheating")

        # await self.topRod.set(args['temp'])
        # await self.e.dispatch([[self.topRod.reachTemp,args['temp']/2]])

        start = time()
        heatTime = self.topRod.heatingTime(args['temp'])
        end = start + heatTime if heatTime >=0 else self.topRod.coolingTime(args['temp'])

        self.steps[self.currentStep]['startTime'] = start
        self.steps[self.currentStep]['endTime'] = end

        await self.topRod.reachTemp(args['temp'])

        return

    async def cook(self,args):
        self.e.log("Cooking: Cooking")

        # await self.topRod.set(args['topTemp'])

        start = time()
        end = start + args['duration']*10 # *60

        self.steps[self.currentStep]['startTime'] = start
        self.steps[self.currentStep]['endTime'] = end

        await self.topRod.sustainTemp(args['topTemp'],args['duration']*10)

        return

    async def checkpoint(self,args):
        self.e.log("Cooking: Checkpoint")

        start = time()
        end = start + args['maxWaitTime']

        self.steps[self.currentStep]['startTime'] = start
        self.steps[self.currentStep]['endTime'] = end

        await self.sleepTill(end)
        return

    async def notify(self,args):
        self.e.log("Cooking: Notify")
        return

    async def cool(self,args):
        self.e.log("Cooking: Cool")

        self.topRod.off()

        start = time()
        end = start + args['duration'] # *10

        self.steps[self.currentStep]['startTime'] = start
        self.steps[self.currentStep]['endTime'] = end

        await self.sleepTill(end)
        return

    async def pause(self):
        try:
            self.pauseTime = time()
            self.isPaused = True

            self.topRod.off()

            self.e.log("Cooking: Paused")
            return True
        except:
            return False
    
    async def resume(self):
                # steps
        try:
            self.startTime = time() -(self.pauseTime-self.startTime)
            self.endTime = self.endTime + (time()-self.pauseTime)

            self.isPaused = False

            self.e.log("Cooking: Resumed")

            return True
        except Exception as e:
            self.e.err(e)
            return False

    def done(self):
        self.isCooking = False
        self.cooktype = 'Done'
        self.topRod.off()

    async def stop(self):
                # steps
        try:
            self.startTime = 0
            self.endTime = 0
            self.topRod.off()
            self.isPaused = False
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
                if self.isPaused == False:
                    return {
                        'item': self.item,
                        
                        'steps': self.steps,
                        'currentStep': self.currentStep,

                        'cooktype': self.cooktype,
                        'isPaused': self.isPaused,
                        'isCooking': self.isCooking,
                        'pauseTime': 0,
                    }
                else:
                    return {
                        'item': self.item,

                        'steps': self.steps,
                        'currentStep': self.currentStep,

                        'cooktype': self.cooktype,
                        'isPaused': self.isPaused,
                        'isCooking': self.isCooking,
                        'pauseTime': self.pauseTime,
                    }
            else:
                return {
                    'steps': self.steps,
                    'currentStep': self.currentStep,

                    'cooktype': self.cooktype,
                    'isPaused': self.isPaused,
                    'isCooking': self.isCooking,
                }
        except Exception as e:
            self.e.log(e)
            return {
                'error': str(e)
            }

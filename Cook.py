from asyncio.tasks import sleep
from time import time
import RodControl
from board import D12
from DB import DB


class Cook:
    def __init__(self, e):
        self.e = e
        self.SIGPAUSE = False
        self.SIGTERM = False
        self.isCooking = False
        self.isDone = False
        self.rod = RodControl.RodControl(D12, e)

        self.steps = None
        self.currentStep = -1
        self.item = 'Empty'

    async def init(self):
        self.db = DB('./db/FoodDB.json')

    async def cookingHandler(self):
        while not self.e._SIGKILL:
            if not self.isCooking and self.steps and self.currentStep == -1:
                try:
                    self.isCooking = True
                    self.SIGTERM = False
                    self.isDone = False

                    for s in range(len(self.steps)):
                        self.currentStep = s
                        step = self.steps[s]

                        step['isDone'] = False

                        while not self.e._SIGKILL and not self.SIGTERM and not step['isDone']:
                            await getattr(self, step['type'])(step)
                            while self.SIGPAUSE and not self.e._SIGKILL and not self.SIGTERM:
                                await sleep(0.5)

                        if self.e._SIGKILL or self.SIGTERM:
                            break

                    self.done()

                except Exception as e:
                    self.e.err(e)
            else:
                await sleep(0.7)

    async def startFromDB(self, item):
        if not self.isCooking:
            self.item = item
            st = self.db._get(item).copy()['steps']
            for s in st:
                try:
                    if 'startTime' in s:
                        del s['startTime']
                    if 'endTime' in s:
                        del s['endTime']
                    if 'pauseTime' in s:
                        del s['pauseTime']
                    if 'isDone' in s:
                        del s['isDone']
                except:
                    self.e.err("Cook: Cleaning Error")
            self.steps = st
            await sleep(1)

            return True
        return False

    async def startFromSteps(self, args):
        if not self.isCooking:
            self.item = args['item']
            filterKeys = {'startTime','endTime','pauseTime','isDone'}
            steps = []
            for s in args['steps']:
                steps.append({x: s[x] for x in s if x not in filterKeys})

            self.steps = steps
            await sleep(0.7)

            return True
        return False

    async def startFromSimple(self, args):
        if not self.isCooking:
            self.item = args['item']
            self.steps = []

            self.steps.append({
                'type': 'preheat',
                'temp': args['temp']
            })
            self.steps.append({
                'type': 'cook',
                'topTemp': args['temp'],
                'bottomTemp': args['temp'],
                'duration': args['time'],
            })
            await sleep(0.7)

            return True
        return False

    async def sleepTill(self, end):
        while time() <= end and not self.e._SIGKILL:
            await sleep(1)

    async def preheat(self, s):
        s['startTime'] = time()
        if await self.e.config.get('cookingVerboseLogs'):
            self.e.log("Cooking: Preheating")

        await self.e.dispatch([
            [self.rod.reachTemp, s['temp']],
            [getattr(self.e.display, s['type']), self.currentStep, self.steps]
        ])

        s['isDone'] = True

        return

    async def cook(self, s):
        duration = s['duration'] * (2 if self.e.config._get('demoMode') else 60)
        if await self.e.config.get('cookingVerboseLogs'):
            self.e.log("Cooking: Cooking {}".format(duration))

        if 'pauseTime' not in s:
            s['startTime'] = time()
            s['endTime'] = s['startTime'] + duration
        else:
            del s['pauseTime']

        await self.e.dispatch([
            [self.rod.sustainTemp, s['topTemp'], s['endTime']],
            [getattr(self.e.display, s['type']), self.currentStep, self.steps],
            [self.e.history.add, self.item, self.steps.copy(), s['topTemp'] if s['topTemp'] > s['bottomTemp'] else s['bottomTemp'], s['duration']]
        ])

        if time() > s['endTime']:
            s['isDone'] = True

        return

    async def checkpoint(self, s):
        if await self.e.config.get('cookingVerboseLogs'):
            self.e.log("Cooking: Checkpoint")

        s['startTime'] = time()
        s['endTime'] = s['startTime'] + s['timeout']

        await self.e.dispatch([
            [self.sleepTill, s['endTime']],
            [getattr(self.e.display, s['type']), self.currentStep, self.steps]
        ])

        s['isDone'] = True
        return

    async def notify(self, s):
        if await self.e.config.get('cookingVerboseLogs'):
            self.e.log("Cooking: Notify")
        s['startTime'] = time()
        s['endTime'] = s['startTime'] + 3
        await self.e.dispatch([
            [self.sleepTill, s['endTime']],
            [getattr(self.e.display, s['type']), self.currentStep, self.steps]
        ])

        s['isDone'] = True
        return

    async def cool(self, s):
        if await self.e.config.get('cookingVerboseLogs'):
            self.e.log("Cooking: Cool")
        s['startTime'] = time()

        self.rod.off()
        s['endTime'] = s['startTime'] + s['duration'] * (2 if self.e.config._get('demoMode') else 60)

        await self.e.dispatch([
            [self.sleepTill, s['endTime']],
            [getattr(self.e.display, s['type']), self.currentStep, self.steps]
        ])
        s['isDone'] = True
        return

    async def pause(self, s=None):
        if self.SIGPAUSE:
            return True
        try:
            self.e.log("Cooking: Paused")
            self.steps[self.currentStep]['pauseTime'] = time()
            self.SIGPAUSE = True

            self.rod.off()

            await self.e.display.pause(self.currentStep, [s['type'] for s in self.steps])

            return True
        except:
            return False

    async def resume(self):
        if not self.SIGPAUSE:
            return True
        try:
            s = self.steps[self.currentStep]
            s['startTime'] = time() - (s['pauseTime']-s['startTime'])
            s['endTime'] = s['endTime'] + (time()-s['pauseTime'])

            self.SIGPAUSE = False
            self.e.log("Cooking: Resumed")

            return True
        except Exception as e:
            self.e.err(e)
            return False

    def done(self):
        if self.isCooking:
            self.SIGTERM = True
            self.rod.off()
            self.isCooking = False
            self.isDone = True
            self.SIGPAUSE = False

            self.steps = None
            self.currentStep = -1
            self.item = 'Empty'
            self.e.display.done()

            self.e.audio._play()

    async def stop(self):
        try:
            self.done()
            self.e.log("Cooking: Stopped")

            return True
        except Exception as e:
            self.e.err(e)
            return False

    async def poweroff(self):
        self.e.poweroff()

    async def nextStep(self):
        if self.currentStep == len(self.steps)-1:
            return False
        try:
            self.SIGPAUSE = True
            self.rod.off()
            self.steps[self.currentStep]['isDone'] = True
            self.SIGPAUSE = False

            return True
        except Exception as e:
            self.e.err(e)
            return False

    async def prevStep(self):
        if self.currentStep == 0:
            return False
        try:
            self.SIGPAUSE = True
            self.rod.off()
            s = self.steps[self.currentStep]
            s['isDone'] = False
            del s['startTime']
            del s['endTime']
            if 'pauseTime' in s:
                del s['pauseTime']
            self.currentStep -= 1
            if 'pauseTime' in s:
                del self.steps[self.currentStep]['pauseTime']

            self.SIGPAUSE = False

            return True
        except Exception as e:
            self.e.err(e)
            return False

    async def setTemp(self, index, temp):
        try:
            if self.isCooking:
                self.SIGPAUSE = True
                self.rod.off()
                s = self.steps[index]
                s['pauseTime'] = time()
                await sleep(0.2)
                t = int(temp)
                if s['type'] == 'preheat':
                    s['temp'] = t
                elif s['type'] == 'cook':
                    s['topTemp'] = t
                    s['bottomTemp'] = t
                self.SIGPAUSE = False
                self.e.log("setTemp: {}".format(self.steps[index]))
                return True
            return False
        except Exception as e:
            self.e.err(e)
            return False

    async def setTime(self, index, t):
        try:
            if self.isCooking:
                s = self.steps[index]
                self.SIGPAUSE = True
                self.rod.off()
                s['pauseTime'] = time()
                await sleep(0.2)
                d = int(t) * (2 if self.e.config._get('demoMode') else 60)
                s['endTime'] = s['startTime'] + d - (time() - s['startTime'])
                if s['type'] == 'cook' or s['type'] == 'cool':
                    s['duration'] = d
                elif s['type'] == 'checkpoint':
                    s['timeout'] = d
                self.SIGPAUSE = False
                self.e.log("setTime: {}".format(self.steps[index]))
                return True
            return False
        except Exception as e:
            self.e.err(e)
            return False

    async def get(self):
        try:
            return {
                'item': self.item,
                'steps': self.steps,
                'currentStep': self.currentStep,
                'currentTempTop': self.rod.get(),
                'currentTempBottom': self.rod.get(),
                'isPaused': self.SIGPAUSE,
                'isCooking': self.isCooking,
                'isDone': self.isDone
            }
        except Exception as e:
            self.e.log(e)
            return {
                'error': str(e)
            }

    def getStep(self, index):
        return self.steps[index] if self.steps else None

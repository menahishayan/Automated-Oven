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
        self.topRod = RodControl.RodControl(D12, e)

        self.steps = None
        self.currentStep = -1
        self.item = 'Empty'

    async def init(self):
        self.db = DB('./FoodDB.json')

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
                            await self.e.dispatch([
                                [getattr(self, step['type']),step],
                                [getattr(self.e.display, step['type']),self.currentStep, self.steps]
                            ])
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
            self.steps = self.db._get(item).copy()['steps']
            await sleep(1)

            return True
        return False

    async def startCustom(self, args):
        if not self.isCooking:
            self.item = 'Custom'
            self.steps = []

            if args['preheat']:
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
            await sleep(1)

            return True
        return False

    async def sleepTill(self, end):
        while time() <= end and not self.e._SIGKILL:
            await sleep(1)

    async def preheat(self, s):
        s['startTime'] = time()
        self.e.log("Cooking: Preheating")

        heatTime = self.topRod.heatingTime(s['temp'])
        end = s['startTime'] + (heatTime if heatTime >= 0 else self.topRod.coolingTime(s['temp']))

        s['endTime'] = end

        await self.topRod.reachTemp(s['temp'])

        if time() > end:
            s['isDone'] = True

        return

    async def cook(self, s):
        duration = s['duration'] * (10 if self.e.config._get('demoMode') else 60)
        self.e.log("Cooking: Cooking {}".format(duration))

        if 'pauseTime' not in s:
            s['startTime'] = time()
            s['endTime'] = s['startTime'] + duration
        else:
            del s['pauseTime']

        await self.topRod.sustainTemp(s['topTemp'], s['endTime'])

        if time() > s['endTime']:
            s['isDone'] = True

        return

    async def checkpoint(self, s):
        self.e.log("Cooking: Checkpoint")

        s['startTime'] = time()
        s['endTime'] = s['startTime'] + s['maxWaitTime']
        await self.sleepTill(s['endTime'])

        s['isDone'] = True
        return

    async def notify(self, s):
        self.e.log("Cooking: Notify")
        s['isDone'] = True
        return

    async def cool(self, s):
        self.e.log("Cooking: Cool")
        s['startTime'] = time()

        self.topRod.off()
        s['endTime'] = s['startTime'] + s['duration'] * (10 if self.e.config._get('demoMode') else 60)

        await self.sleepTill(s['endTime'])
        s['isDone'] = True
        return

    async def pause(self, s=None):
        if self.SIGPAUSE:
            return True
        try:
            self.e.log("Cooking: Paused")
            self.steps[self.currentStep]['pauseTime'] = time()
            self.SIGPAUSE = True

            self.topRod.off()

            await self.e.display.pause(self.currentStep,[s['type'] for s in self.steps])

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
        self.SIGTERM = True
        self.topRod.off()
        self.isCooking = False
        self.isDone = True
        self.SIGPAUSE = False

        self.steps = None
        self.currentStep = -1
        try:
            self.e.audio.play()
        except Exception as e:
            self.e.err(e)

    async def stop(self):
        try:
            self.done()
            self.e.log("Cooking: Stopped")

            return True
        except Exception as e:
            self.e.err(e)
            return False

    async def nextStep(self):
        if self.currentStep == len(self.steps)-1:
            return False
        try:
            self.SIGPAUSE = True
            self.topRod.off()
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
            self.topRod.off()
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

    async def setTemp(self, _type, temp):
        try:
            if self.isCooking:
                self.SIGPAUSE = True
                s = self.steps[self.currentStep]
                if _type == 'preheat':
                    if s['type'] == 'preheat':
                        s['temp'] = int(temp)
                elif _type == 'top':
                    if s['type'] == 'cook':
                        s['topTemp'] = int(temp)
                elif _type == 'bottom':
                    if s['type'] == 'cook':
                        s['bottomTemp'] = int(temp)
                self.SIGPAUSE = False
                # change in actual rod value
                return True
            return False
        except Exception as e:
            self.e.err(e)
            return False

    async def setTime(self, t):
        try:
            if self.isCooking:
                s = self.steps[self.currentStep]
                if s['type'] == 'cook':
                    d = int(t) * (10 if self.e.config._get('demoMode') else 60)
                    if 'pauseTime' in s:
                        s['endTime'] = d - (s['pauseTime'] - s['startTime'])
                        s['duration'] = d
                    else:
                        self.topRod.off()
                        self.SIGPAUSE = True
                        s['duration'] = d
                        self.SIGPAUSE = False
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
                'currentTempTop': self.topRod.get(),
                'isPaused': self.SIGPAUSE,
                'isCooking': self.isCooking,
            }
        except Exception as e:
            self.e.log(e)
            return {
                'error': str(e)
            }

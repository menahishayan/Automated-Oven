from digitalio import DigitalInOut, Direction
from asyncio import sleep
from time import time
from math import log, exp

class RodControl:
    def __init__(self, pin, e):
        self.pin = DigitalInOut(pin)
        self.pin.direction = Direction.OUTPUT 
        self.pin.value = False

        self.e = e
        self.surroundingTemp = int(e.temp)

        if self.e.config.has('lastHeatTemp'):
            self.currentTemp = self.e.config._get('lastHeatTemp')
            self.lastHeatTime = self.e.config._get('lastHeatTime')
        else:
            self.currentTemp = int(e.temp)
            self.lastHeatTime = 0

        self.isAdjusting = False
        self.isSustaining = False

        self.SIGKILLADJUST = False
        self.SIGKILLSUSTAIN = False


    def heatingTime(self,temp):
        return (0.36*(temp-self.currentTemp)) - 0.626 +1

    def heatingTemp(self,_time):
        return self.currentTemp + (_time * 2.778)

    def coolingTime(self,temp):
        return log((self.currentTemp - self.surroundingTemp)/(temp - self.surroundingTemp))/0.008

    def coolingTemp(self,_time):
        return self.surroundingTemp + (self.currentTemp - self.surroundingTemp)*exp(-0.008*_time)

    async def sleep(self,_time,adjust, cool=False):
        start = time()
        while time()-start <= _time:
            if self.SIGKILLADJUST or self.SIGKILLSUSTAIN or self.e._SIGKILL:
                break

            # if round(time()-start)%10 == 0:
                # self.e.log("Thermals: {} @ {} ({},{})".format(round(self.currentTemp),round(time()-start),"Adjust" if adjust else "Sustain","Cool" if cool else "Heat"))

            await sleep(0.3)
            if not cool:
                self.currentTemp = self.heatingTemp(0.3)
            else:
                self.currentTemp = self.coolingTemp(0.3)

    async def heat(self,temp,adjust=False):
        self.pin.value = True
        await self.sleep(self.heatingTime(temp),adjust=adjust)
        self.lastHeatTime = time()
        self.e.config.set('lastHeatTemp',self.currentTemp)
        self.e.config.set('lastHeatTime',time())
        self.pin.value = False

    async def cool(self,temp,adjust=False):
        self.pin.value = False
        await self.sleep(self.coolingTime(temp),cool=True,adjust=adjust)

    async def set(self,temp):
        await self.e.dispatch([[self.reachTemp,temp]])

    async def reachTemp(self,temp):
        if temp == 0:
            temp = self.surroundingTemp

        if self.isSustaining:
            self.SIGKILLSUSTAIN = True
            await sleep(0.3)
        elif self.isAdjusting:
            self.SIGKILLADJUST = True
            await sleep(0.3)

        self.isAdjusting = True

        self.SIGKILLADJUST = False
        self.SIGKILLSUSTAIN = False

        if self.lastHeatTime > 0:
            self.currentTemp = self.coolingTemp(time() - self.lastHeatTime)

        if temp > round(self.currentTemp):
            await self.heat(temp,adjust=True)

        elif temp < round(self.currentTemp):
            await self.cool(temp,adjust=True)

        self.isAdjusting = False

    async def sustainTemp(self,temp,end):
        if self.isSustaining:
            self.SIGKILLSUSTAIN = True
            await sleep(0.3)
        elif self.isAdjusting:
            self.SIGKILLADJUST = True
            await sleep(0.3)

        self.isSustaining = True

        self.SIGKILLADJUST = False
        self.SIGKILLSUSTAIN = False

        if temp == 0:
            temp = self.surroundingTemp

        if self.lastHeatTime > 0:
            self.currentTemp = self.coolingTemp(time() - self.lastHeatTime)

        while round(time()) < round(end) and not self.SIGKILLSUSTAIN and not self.e._SIGKILL:
            if round(self.currentTemp) > temp:
                if(self.coolingTime(temp-8) + time() > end):
                    self.e.log("Compromise: Req: {} End: {}".format(self.coolingTime(temp-8) + time(),end))
                    compromiseTemp = self.coolingTemp(round(end-time()))
                    await self.cool(compromiseTemp)
                else:
                    await self.cool(temp-8)
            elif round(self.currentTemp) < temp:
                if(self.heatingTime(temp) + time() > end):
                    self.e.log("Compromise: Req: {} End: {}".format(self.heatingTime(temp) + time(),end))
                    compromiseTemp = self.heatingTemp(round(end-time()))
                    await self.heat(compromiseTemp)
                else:
                    await self.heat(temp)

        self.isSustaining = False
        self.SIGKILLSUSTAIN = False

    def off(self):
        self.SIGKILLADJUST = True
        self.SIGKILLSUSTAIN = True

    def isOn(self):
        return self.pin.value

    def get(self):
        return round(self.currentTemp,1)

    def __str__(self):
        return str(self.get())

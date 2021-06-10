from digitalio import DigitalInOut, Direction
from asyncio import sleep
from time import time
from math import log, exp

class RodControl:
    def __init__(self, pin, e, maxTemp=250):
        self.pin = DigitalInOut(pin)
        self.pin.direction = Direction.OUTPUT 
        self.pin.value = False

        self.maxTemp = int(maxTemp)
        self.e = e
        self.currentTemp = int(e.temp)
        self.surroundingTemp = int(e.temp)

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
                if adjust:
                    self.isAdjusting = False
                else:
                    self.isSustaining = False
                self.SIGKILLADJUST = self.SIGKILLSUSTAIN = False
                break

            if round(time()-start)%5 == 0:
                self.e.log("Thermals: {} @ {} ({},{})".format(round(self.currentTemp),round(time()-start),"Adjust" if adjust else "Sustain","Cool" if cool else "Heat"))

            await sleep(1)
            if not cool:
                self.currentTemp = self.heatingTemp(1)
            else:
                self.currentTemp = self.coolingTemp(1)

    async def heat(self,temp,adjust=False):
        self.pin.value = True
        await self.sleep(self.heatingTime(temp),adjust=adjust)
        self.pin.value = False

    async def cool(self,temp,adjust=False):
        self.pin.value = False
        await self.sleep(self.coolingTime(temp),cool=True,adjust=adjust)

    async def reachTemp(self,temp):
        if temp == 0:
            self.pin.value = False


        if self.isSustaining:
            self.SIGKILLSUSTAIN = True
            await sleep(1)
        elif self.isAdjusting:
            self.SIGKILLADJUST = True
            await sleep(1)

        self.isAdjusting = True

        if temp > round(self.currentTemp):
            self.e.log("Thermals: To Heat {} from {} in {} s".format(temp,round(self.currentTemp),round(self.heatingTime(temp))))
            await self.heat(temp,adjust=True)

        elif temp < round(self.currentTemp):
            self.e.log("Thermals: To Cool {} from {} in {} s".format(temp,round(self.currentTemp),round(self.coolingTime(temp))))
            await self.cool(temp,adjust=True)

        self.isAdjusting = False
        await self.e.dispatch([[self.sustainTemp,temp]])

    async def sustainTemp(self,temp):
        if self.isSustaining:
            self.SIGKILLSUSTAIN = True
            await sleep(1)
        elif self.isAdjusting:
            self.SIGKILLADJUST = True
            await sleep(1)

        self.isSustaining = True

        # while not self.SIGKILLSUSTAIN and not self.e._SIGKILL:
        for i in range(4):
            if round(self.currentTemp) >= temp:
                await self.cool(temp-8)
            elif round(self.currentTemp) < temp:
                await self.heat(temp)

        self.isSustaining = False
        self.SIGKILLSUSTAIN = False

    def stop(self):
        self.SIGKILLADJUST = True
        self.SIGKILLSUSTAIN = True

    def get(self):
        return round(self.currentTemp)

    def __str__(self):
        return str(self.get())

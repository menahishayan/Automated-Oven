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

        self.isPreheating = False
        self.isSustaining = False

        self.SIGKILLPREHEAT = False
        self.SIGKILLSUSTAIN = False

    def heatingTime(self,temp):
        return (0.36*(temp-self.currentTemp)) - 0.626

    def heatingTemp(self,_time):
        return (_time +0.626)/0.36

    def coolingTime(self,temp):
        return log((self.currentTemp - self.surroundingTemp)/(temp - self.surroundingTemp))/0.008

    def coolingTemp(self,_time):
        return self.surroundingTemp + (self.currentTemp - self.surroundingTemp)*exp(-0.008*_time)

    async def sleep(self,_time,preheat, cool=False):
        start = time()
        while time()-start <= _time:
            if self.SIGKILLPREHEAT or self.SIGKILLSUSTAIN or self.e._SIGKILL:
                if preheat:
                    self.isPreheating = False
                else:
                    self.isSustaining = False
                self.SIGKILLPREHEAT = self.SIGKILLSUSTAIN = False
                break

            if(time()-start)%5 == 0:
                self.e.log("Thermals: {} @ {} ({},{})".format(round(self.currentTemp),round(time()-start),"Preheat" if preheat else "Sustain","Cool" if cool else "Heat"))

            await sleep(1)
            if not cool:
                self.currentTemp = self.heatingTemp(time()-start) + self.surroundingTemp
            else:
                self.currentTemp = self.coolingTemp(1)

    async def heat(self,temp,preheat=False):
        self.pin.value = True
        await self.sleep(self.heatingTime(temp),preheat=preheat)
        self.pin.value = False

    async def cool(self,temp,preheat=False):
        self.pin.value = False
        await self.sleep(self.coolingTime(temp),cool=True,preheat=preheat)

    async def reachTemp(self,temp):
        if temp == 0:
            self.pin.value = False

        self.e.log("Thermals: To Reach {} from {} in {} s".format(temp,round(self.currentTemp),round(self.heatingTime(temp))))

        if self.isSustaining:
            self.SIGKILLSUSTAIN = True
            await sleep(1)
        elif self.isPreheating:
            self.SIGKILLPREHEAT = True
            await sleep(1)

        self.isPreheating = True

        if temp > round(self.currentTemp):
            await self.heat(temp,preheat=True)

        elif temp < round(self.currentTemp):
            await self.cool(temp,preheat=True)

        self.isPreheating = False
        await self.e.dispatch([[self.sustainTemp,temp]])

    async def sustainTemp(self,temp):
        if self.isSustaining:
            self.SIGKILLSUSTAIN = True
            await sleep(1)
        elif self.isPreheating:
            self.SIGKILLPREHEAT = True
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
        self.SIGKILLPREHEAT = True
        self.SIGKILLSUSTAIN = True

    def get(self):
        return round(self.currentTemp)

    def __str__(self):
        return str(self.get())

from pwmio import PWMOut
from asyncio import sleep
from time import time
from math import log

class RodControl:
    def __init__(self, pin, e, maxTemp=250):
        self.pin = PWMOut(pin, duty_cycle=0, frequency=10)
        self.maxTemp = int(maxTemp)
        self.e = e
        self.currentTemp = e.temp

    async def sleep(self,duration,cool=False):
        start = time()
        while(time() <= start+duration):
            self.e.log("ThermodynamicsDebugging: Current temp {0:.1f} at {0:.1f} s elapsed".format(self.currentTemp,time()-start))
            await sleep(0.5)
            if not cool:
                self.currentTemp = ((time()-start)+8.93)/0.137
            else:
                self.currentTemp = ((time()-start)-19.42)/-0.07

    async def cooking(self):
        while self.e.cook.isCooking and not self.e.cook.isPaused:
            await self.sleep((self.currentTemp * 0.137)-8.93)
            self.pin.duty_cycle = 2 ** 15
            await self.sleep((self.currentTemp * -0.07)+19.42,True)
            self.pin.duty_cycle = 0

    async def set(self, temp):
        if temp == 0:
            self.pin.duty_cycle = 0
            return
        elif temp > self.maxTemp:
            temp = self.maxTemp

        diff = temp - self.currentTemp

        self.e.log("ThermodynamicsDebugging: Required {} from {}".format(self.currentTemp,temp))

        if diff == 0:
            return
        elif diff > 0:
            self.pin.duty_cycle = 2 ** 15
            heatTime = (diff*0.36) - 8.13
            self.e.log("ThermodynamicsDebugging: Heating {} to {} in {0:.1f} s".format(self.currentTemp,temp,heatTime))
            await sleep(heatTime)
            self.pin.duty_cycle = 0
            # self.currentTemp = temp
            self.e.dispatch([[self.cooking]])
        else:
            self.pin.duty_cycle = 0
            coolingTime = (log(self.currentTemp - 28) - log(temp - 28))/0.008
            self.e.log("ThermodynamicsDebugging: Cooling {} to {} in {0:.1f} s".format(self.currentTemp,temp,coolingTime))
            await sleep(coolingTime)


    def get(self):
        return round(self.currentTemp)

    def __str__(self):
        return str(self.get())

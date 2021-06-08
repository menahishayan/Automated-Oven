from pwmio import PWMOut
from asyncio import sleep
from time import time
from math import log

class RodControl:
    def __init__(self, pin, e, maxTemp=250):
        self.pin = PWMOut(pin, duty_cycle=0, frequency=10)
        self.maxTemp = int(maxTemp)
        self.e = e
        self.currentTemp = int(e.temp)
        self.e.log("RodControl: Init {}".format(self.currentTemp))

    async def sleep(self,duration,cool=False):
        start = time()
        while(time() <= start+duration):
            self.e.log("ThermodynamicsDebugger: Current temp {} at {} s elapsed".format(self.currentTemp,time()-start))
            await sleep(0.5)
            if not cool:
                self.currentTemp = ((time()-start)+8.93)/0.137
            else:
                self.currentTemp = ((time()-start)-19.42)/-0.07

    async def cooking(self):
        while not self.e._SIGKILL:
            if self.e.cook.isCooking and not self.e.cook.isPaused:
                if self.currentTemp == self.e.cook.top:
                    await self.sleep((self.currentTemp * 0.137)-8.93)
                    self.pin.duty_cycle = 2 ** 15
                    await self.sleep((self.currentTemp * -0.07)+19.42,True)
                    self.pin.duty_cycle = 0
            else:
                await sleep(1)

    async def setTemp(self, temp):
        try:
            if temp == 0:
                self.pin.duty_cycle = 0
                return
            elif temp > self.maxTemp:
                temp = self.maxTemp

            diff = temp - self.currentTemp

            if diff == 0:
                return
            elif diff > 0:
                self.pin.duty_cycle = 2 ** 15
                heatTime = (diff*0.36) - 8.13
                self.e.log("ThermodynamicsDebugger: Heating {} to {} in {} s".format(self.currentTemp,temp,heatTime))
                await sleep(heatTime)
                self.pin.duty_cycle = 0
                # self.currentTemp = temp
                # await self.e.dispatch([[self.cooking]])
            else:
                self.pin.duty_cycle = 0
                coolingTime = (log(self.currentTemp - 28) - log(temp - 28))/0.008
                self.e.log("ThermodynamicsDebugger: Cooling {} to {} in {} s".format(self.currentTemp,temp,coolingTime))
                await sleep(coolingTime)
        except Exception as e:
            self.e.err("error: setTemp: " + e)

    def getTemp(self):
        return round(self.currentTemp)

    def __str__(self):
        return str(self.getTemp())

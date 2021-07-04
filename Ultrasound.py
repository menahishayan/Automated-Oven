import RPi.GPIO as GPIO
from time import time,sleep

class Ultrasound:
    def __init__(self,e):
        self.TRIG = 23
        self.ECHO = 15
        self.e = e

        GPIO.setup(self.TRIG, GPIO.OUT)
        GPIO.setup(self.ECHO, GPIO.IN)

        self.lastUpdatedDistance = 0

    async def get(self):
        GPIO.output(self.TRIG, True)
        sleep(0.00001)
        GPIO.output(self.TRIG, False)

        StartTime = time()
        StopTime = time()

        loopStartTime = time()
        while GPIO.input(self.ECHO) == 0 or time() > loopStartTime+1.5:
            if self.e._SIGKILL:
                return -1
            StartTime = time()

        if time() > loopStartTime+1.5:
            self.lastUpdatedDistance = 9999
            return 9999

        loopStartTime = time()
        while GPIO.input(self.ECHO) == 1 or time() > loopStartTime+1.5:
            if self.e._SIGKILL:
                return -1
            StopTime = time()


        TimeElapsed = StopTime - StartTime

        distance = (TimeElapsed * 34300) / 2

        self.lastUpdatedDistance = round(distance)

        return round(distance)

    def getLastUpdated(self):
        return self.lastUpdatedDistance

    def __str__(self):
        return self.get()
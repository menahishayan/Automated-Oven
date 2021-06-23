import RPi.GPIO as GPIO
from time import time,sleep

class Ultrasound:
    def __init__(self,e):
        self.TRIG = 23
        self.ECHO = 15
        self.e = e

        GPIO.setup(self.TRIG, GPIO.OUT)
        GPIO.setup(self.ECHO, GPIO.IN)

    async def get(self):
        GPIO.output(self.TRIG, True)
        sleep(0.00001)
        GPIO.output(self.TRIG, False)

        StartTime = time()
        StopTime = time()

        while GPIO.input(self.ECHO) == 0:
            if self.e._SIGKILL:
                return -1
            StartTime = time()

        while GPIO.input(self.ECHO) == 1:
            if self.e._SIGKILL:
                return -1
            StopTime = time()

        TimeElapsed = StopTime - StartTime

        distance = (TimeElapsed * 34300) / 2

        return int(distance)

    def __str__(self):
        return self.get()
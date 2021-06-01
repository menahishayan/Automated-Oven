import RPi.GPIO as GPIO
import time

class Ultrasound:
    def __init__(self):
        self.TRIG = 23
        self.ECHO = 15

        GPIO.setup(self.TRIG, GPIO.OUT)
        GPIO.setup(self.ECHO, GPIO.IN)

    async def get(self):
        GPIO.output(self.TRIG, True)
        time.sleep(0.00001)
        GPIO.output(self.TRIG, False)

        StartTime = time.time()
        StopTime = time.time()

        while GPIO.input(self.ECHO) == 0:
            StartTime = time.time()

        while GPIO.input(self.ECHO) == 1:
            StopTime = time.time()

        TimeElapsed = StopTime - StartTime

        distance = (TimeElapsed * 34300) / 2

        return distance

    def __str__(self):
        return self.get()
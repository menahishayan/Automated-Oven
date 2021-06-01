import RPi.GPIO as GPIO
import adafruit_dht
import time
from board import D2


class Temp:
    def __init__(self):
        self.PIN = D2
        self.dhtDevice = adafruit_dht.DHT11(self.PIN, use_pulseio=False)

    async def get(self):
        return self.dhtDevice.temperature

    def __str__(self):
        return self.get()

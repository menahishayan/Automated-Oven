import RPi.GPIO as GPIO
import adafruit_dht
import time
from board import D2
from asyncio import sleep

class Temp:
    def __init__(self):
        self.PIN = D2
        self.dhtDevice = adafruit_dht.DHT11(self.PIN, use_pulseio=False)
        self.value = self.dhtDevice.temperature

    async def update(self):
        try:
            self.value = self.dhtDevice.temperature
        except: 
            return

    def __str__(self):
        return str(self.value)

    def __int__(self):
        return self.value

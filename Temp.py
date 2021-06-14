import adafruit_dht
from board import D2

class Temp:
    def __init__(self):
        self.PIN = D2
        self.dhtDevice = adafruit_dht.DHT11(self.PIN, use_pulseio=False)
        try:
            self.value = self.dhtDevice.temperature
        except: 
            self.value = 28

    async def update(self):
        try:
            self.value = self.dhtDevice.temperature
        except: 
            return

    def __str__(self):
        return str(self.value)

    def __int__(self):
        return self.value

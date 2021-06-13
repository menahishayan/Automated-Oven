import RPi.GPIO as GPIO
import adafruit_dht
import time
from board import D2


class Temp:
    def __init__(self):
        self.PIN = D2
        self.dhtDevice = adafruit_dht.DHT11(self.PIN,use_pulseio=False)

    def get(self):
        return self.dhtDevice.temperature
      
    def __str__(self):
        return self.get()


if __name__ == '__main__':
    t = Temp()
    try:
        while True:
            dist = t.get()
            print("Measured temp = %.1f C" % dist)
            time.sleep(1)

    except KeyboardInterrupt:
        print("Measurement stopped by User")
        GPIO.cleanup()

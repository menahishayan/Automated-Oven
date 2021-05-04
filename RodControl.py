import pwmio

class RodControl:
    def __init__(self, pin, maxTemp):
        self.pin = pwmio.PWMOut(pin, frequency=1000, duty_cycle=0)
        self.maxTemp = int(maxTemp)

    def set(self, temp):
        self.pin.duty_cycle = int((temp/self.maxTemp) * 65535)

    def get(self):
        return int((self.pin.duty_cycle/65535) * self.maxTemp)

    def __str__(self):
        return self.get()
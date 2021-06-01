from pwmio import PWMOut

class RodControl:
    def __init__(self, pin, maxTemp=250):
        self.pin = PWMOut(pin, duty_cycle=2 ** 15, frequency=100, variable_frequency=True)
        self.maxTemp = int(maxTemp)

    def set(self, temp):
        self.pin.frequency = (temp*100)/self.maxTemp

    def get(self):
        return self.pin.frequency

    def __str__(self):
        return str(self.get())
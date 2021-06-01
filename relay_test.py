# import digitalio
import pwmio
from board import *
import time

# led = digitalio.DigitalInOut(D12)
# led.direction = digitalio.Direction.OUTPUT
pwm = pwmio.PWMOut(D12, duty_cycle=2 ** 15, frequency=1, variable_frequency=True)
# d = 0.1
# for i in range(100):
#     led.value = True
#     print(led.value)
#     time.sleep(d)

#     led.value = False
#     print(led.value)
#     time.sleep(d)

pwm.frequency = 5
time.sleep(5)
pwm.frequency = 1
time.sleep(5)

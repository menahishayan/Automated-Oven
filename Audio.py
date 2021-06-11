from os import name, system  
from subprocess import PIPE, run

class Audio:
    def __init__(self):
        self.volume = int(self.readVolume())
        # self.volume = 50

    def readVolume(self):
        result = run('amixer -M sget Headphone', stdout=PIPE, stderr=PIPE, universal_newlines=True, shell=True)
        print(result)
        return result.stdout.split(-1)

    def getVolume(self):
        return self.volume

    def setVolume(self,vol):
        system("amixer -q -M sset Headphone {}%".format(vol))
        self.volume = vol

    def play(self):
        system('aplay ./CantinaBand3.wav')

if __name__ == '__main__':
    a = Audio()
    a.readVolume()
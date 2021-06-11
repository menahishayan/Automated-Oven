from os import system  
from subprocess import PIPE, run

class Audio:
    def __init__(self):
        try:
            self.volume = int(self.readVolume())
        except:
            self.volume = 50

    def readVolume(self):
        result = run('amixer -M sget Headphone', stdout=PIPE, stderr=PIPE, universal_newlines=True, shell=True)
        res = int(str(result.stdout).split('[')[1].split('%')[0])
        return res

    def getVolume(self):
        return self.volume

    def setVolume(self,vol):
        run("amixer -q -M sset Headphone {}%".format(vol))
        self.volume = vol

    def play(self):
        run('aplay ./audio/Chime.wav')

if __name__ == '__main__':
    a = Audio()
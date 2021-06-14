from os import system  
from subprocess import PIPE, run

class Audio:
    def __init__(self,e):
        try:
            self.volume = int(self.readVolume())
            self.e = e
            self.selectedTone = e.config._get('selectedTone') if e.config.has('selectedTone') else 'Chime'
        except:
            self.volume = 50

    def readVolume(self):
        result = run('amixer -M sget Headphone', stdout=PIPE, stderr=PIPE, universal_newlines=True, shell=True)
        res = int(str(result.stdout).split('[')[1].split('%')[0])
        return res

    async def getVolume(self):
        return self.volume

    async def getAvailableTones(self):
        result = run('ls /home/pi/OS/audio/', stdout=PIPE, stderr=PIPE, universal_newlines=True, shell=True)
        res = str(result.stdout).split("\n")
        return [r.split('.wav')[0] for r in res]

    async def getSelectedTone(self):
        return self.selectedTone

    async def setSelectedTone(self,name):
        self.selectedTone = name
        await self.play()
        self.e.config.set('selectedTone',name)

    async def setVolume(self,vol):
        system("amixer -q -M sset Headphone {}%".format(vol))
        self.volume = vol

    async def play(self):
        system('aplay audio/{}.wav'.format(self.selectedTone))

    def _play(self):
        system('aplay audio/{}.wav'.format(self.selectedTone))

# if __name__ == '__main__':
#     a = Audio('Chime')
#     a.play()
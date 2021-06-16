from SimpleWebSocketServer import WebSocket
import json
from asgiref.sync import async_to_sync
from os import system
from subprocess import PIPE, run

class WebSocketServer(WebSocket):
    def init(self, e):
        self.e = e

    def handleMessage(self):
        req = json.loads(self.data)
        res = {
            'type': 'none'
        }
        try:
            fn = getattr(self, req['function']) if req['module'] == 'other' else getattr(getattr(self.e, req['module']), req['function'])
            var = async_to_sync(fn)(*req['params']) if 'params' in req else async_to_sync(fn)()
            res = {
                'type': 'result',
                'req': req['function'],
                'result': var
            }
            var = async_to_sync(fn)(*req['params']) if 'params' in req else async_to_sync(fn)()
            res = {
                'type': 'result',
                'req': req['function'],
                'result': var
            }
        except Exception as e:
            res = {
                'type': 'error',
                'req': req['function'],
                'error': str(e)
            }
        self.sendMessage(json.dumps(res))

    async def setUserName(self,name):
        name = name.capitalize()
        await self.e.users.add(name)
        return True

    async def getLogs(self):
        logs = [""]
        with open('./logfile.log') as log:
            logs = log.readlines()
        return logs

    async def restart(self):
        system('sudo reboot')
        return True

    async def poweroff(self):
        system('sudo shutdown -h now')
        return True

    async def update(self):
        system('~/OS/update.sh | at now')
        return True

    async def getAvailableModels(self):
        result = run('ls /home/pi/keras/models', stdout=PIPE, stderr=PIPE, universal_newlines=True, shell=True)
        res = str(result.stdout).split("\n")
        modelList = [r for r in res if r.startswith('v')]
        return modelList

    async def getVersion(self):
        return self.e.__version__

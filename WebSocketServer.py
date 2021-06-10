from SimpleWebSocketServer import WebSocket
import json
from asgiref.sync import async_to_sync


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
        with open('./users.json') as db:
            db = json.load(db)
            if name in db:
                db[name].append(self.address)
            else:
                db[name] = [self.address]
        return True

    async def getLogs(self):
        logs = ""
        with open('./logfile.log') as log:
            logs = log
        return logs

    # def handleConnected(self):
    #     self.e.log("Socket: {} Connected".format(list(self.address)[0]))

    # def handleClose(self):
    #     print(self.address, 'closed')

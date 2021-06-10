from SimpleWebSocketServer import WebSocket
from json import loads, dumps
from asgiref.sync import async_to_sync

class WebSocketServer(WebSocket):
    def init(self,e):
        self.e = e

    def handleMessage(self):
        req = loads(self.data)
        res = {
            'type': 'none'
        }
        try:
            fn = getattr(getattr(self.e,req['module']), req['function'])
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
        self.sendMessage(dumps(res))

    # def handleConnected(self):
    #     self.e.log("Socket: {} Connected".format(list(self.address)[0]))

    # def handleClose(self):
    #     print(self.address, 'closed')
from SimpleWebSocketServer import WebSocket
import json
import History
import Energy
from asgiref.sync import async_to_sync

class WebSocketServer(WebSocket):
    def init(self,e):
        self.e = e
        # print(self.e)

    def handleMessage(self):
        req = json.loads(self.data)
        if req['msg'] == 'method':
            try:
                self.sendMessage(getattr(self, req['method'])())
            except Exception as e:
                res = {
                    'msg': 'error',
                    'error': str(e),
                    'code': 501
                }
                self.sendMessage(json.dumps(res))
        elif req['msg'] == 'direct':
            try:
                if 'params' in req:
                    self.sendMessage(getattr(self, req['module'])(req['function'],*req['params']))
                else:
                    self.sendMessage(getattr(self, req['module'])(req['function']))
            except Exception as e:
                res = {
                    'msg': 'error',
                    'error': str(e),
                    'code': 501
                }
                self.sendMessage(json.dumps(res))
        else:
            res = {
                'msg': 'error',
                'error': 'unrecognized request',
                'code': 501
            }
            self.sendMessage(json.dumps(res))
        
    def energy(self, _fn, *params):
        try:
            fn = getattr(self.e.energy, _fn)
            var = async_to_sync(fn)(*params)
            res = {
                'msg': 'result',
                'req': str(_fn),
                'result': var
            }
            return json.dumps(res)
        except Exception as e:
            res = {
                'msg': 'error',
                'req': str(_fn),
                'error': str(e)
            }
            return json.dumps(res)

    def history(self, _fn, *params):
        try:
            fn = getattr(self.e.history, _fn)
            var = async_to_sync(fn)(*params)
            res = {
                'msg': 'result',
                'req': str(_fn),
                'result': var
            }
            return json.dumps(res)
        except Exception as e:
            res = {
                'msg': 'error',
                'req': str(_fn),
                'error': str(e)
            }
            return json.dumps(res)

    def cook(self, _fn, *params):
        try:
            fn = getattr(self.e.cook, _fn)
            var = async_to_sync(fn)(*params)
            res = {
                'msg': 'result',
                'req': str(_fn),
                'result': var
            }
            return json.dumps(res)
        except Exception as e:
            res = {
                'msg': 'error',
                'req': str(_fn),
                'error': str(e)
            }
            return json.dumps(res)

    def display(self, _fn, *params):
        try:
            fn = getattr(self.e.display, _fn)
            var = async_to_sync(fn)(*params)
            res = {
                'msg': 'result',
                'req': str(_fn),
                'result': var
            }
            return json.dumps(res)
        except Exception as e:
            res = {
                'msg': 'error',
                'req': str(_fn),
                'error': str(e)
            }
            return json.dumps(res)
            
    # def handleConnected(self):
    #     print(self.address, 'connected')

    # def handleClose(self):
    #     print(self.address, 'closed')
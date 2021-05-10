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
        else:
            res = {
                'msg': 'error',
                'error': 'unrecognized request',
                'code': 501
            }
            self.sendMessage(json.dumps(res))
        
    def getHistory(self):
        h = History.History('/home/pi/OS/HistoryDB.json')
        res = {
            'msg': 'result',
            'result': h.get()
        }
        return json.dumps(res)

    def getEnergy(self):
        e = Energy.Energy('/home/pi/OS/EnergyDB.json')
        # if not req['params']:
        res = {
            'msg': 'result',
            'result': e.get()
        }
        # else:
        #     resultArray = []
        #     params = req['params']
        #     if len(params) > 0:
        #         for p in params:
        #             resultArray.append(e.get(p))
        #     res = {
        #         'msg': 'result',
        #         'result': resultArray
        #     }
        return json.dumps(res)

    def getCooking(self):
        c = self.e.cook
        # getData = c.get()
        # self.e.log("getData: " + str(getData))
        res = {
            'msg': 'result',
            'result': c.get()
        }
        return json.dumps(res)

    def pauseCooking(self):
        try:
            var = async_to_sync(self.e.cook.pause)()
            self.e.log(var)
            res = {
                'msg': 'result',
                # 'result': str(var).replace('\'','\"')
                'result': var
            }
            return json.dumps(res)
        except Exception as e:
            res = {
                'msg': 'result',
                'result': str(e)
            }
            return json.dumps(res)

    def resumeCooking(self):
        try:
            var = async_to_sync(self.e.cook.resume)()
            res = {
                'msg': 'result',
                'result': var
            }
            return json.dumps(res)
        except Exception as e:
            res = {
                'msg': 'result',
                'result': str(e)
            }
            return json.dumps(res)
            
    # def handleConnected(self):
    #     print(self.address, 'connected')

    # def handleClose(self):
    #     print(self.address, 'closed')
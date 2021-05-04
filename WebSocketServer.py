import asyncio
import websockets
import json
import pathlib
import ssl
import History
import Energy

class WebSocketServer:
    def __init__(self, port=8069):
        self.__version__ = '0.1.2'
        start_server = websockets.serve(
            self.server, "oven.local", port
        )

        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()

    async def server(self,websocket, path):
        req = await websocket.recv()

        req = json.loads(req)

        if req['msg'] == 'method':
            if req['method'] == 'getHistory':
                h = History.History('/home/pi/OS/HistoryDB.json')
                res = {
                    'msg': 'result',
                    'result': h.get()
                }
                await websocket.send(json.dumps(res))
            if req['method'] == 'getEnergy':
                e = Energy.Energy('/home/pi/OS/EnergyDB.json')
                res = {
                    'msg': 'result',
                    'result': e.get()
                }
                await websocket.send(json.dumps(res))
            else:
                res = {
                    'msg': 'error',
                    'error': 'unrecognized request',
                    'code': 501
                }
                await websocket.send(json.dumps(res))
        print("sent response")

# context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
# context.load_cert_chain(certfile= "cert.pem", keyfile= "key.pem")

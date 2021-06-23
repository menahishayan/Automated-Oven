from time import time
from asyncio import sleep
from DB import DB

class Automations(DB):
    def __init__(self, e, dbPath='./db/AutomationsDB.json'):
        super().__init__(dbPath)
        self.e = e
    
    async def delete(self,k):
        del self.db[k]
        self.flush()

    async def run(self,k):
        if self.e.cook.isCooking:
            self.e.cook.stop()
            sleep(0.7)
        self.db[k]['lastUsed'] = round(time())
        self.flush()
        self.e.cook.startFromSteps(self.db[k])

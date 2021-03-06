import time
from datetime import datetime
from asyncio import sleep
from DB import DB


class Energy(DB):
    def __init__(self, e, dbPath='./db/EnergyDB.json'):
        super().__init__(dbPath)
        self.e = e
        self.lastUpdatedValueNow = 0

    async def add(self, entry):
        try:
            date = datetime.now().strftime("%Y-%m-%d")
            if date not in self.db:
                self.db[date] = {}

            self.db[date][str(round(time.time()))] = {
                'watts': round(entry,2),
                'users': await self.e.users.get()
            }
            self.flush()

        except Exception as e:
            self.e.err(e)

    async def getAll(self, date=""):
        if len(date) > 0:
            try:
                return self.db[date]
            except:
                return self.db
        return self.db

    async def logEnergy(self):
        while not self.e._SIGKILL:
            interval = await self.config.get('energyInterval')
            aggregate = []
            for _ in range(interval):
                aggregate.append(self.detect())
                await sleep(interval)

            self.lastUpdatedValueNow = round(sum(aggregate)/interval)

            await self.add(self.lastUpdatedValueNow/(3600/interval))
        

    def detect(self):
        base = 15
        if self.e.cook.rod.isOn():
            base += 650
        return base

    async def getNow(self):
        return self.lastUpdatedValueNow

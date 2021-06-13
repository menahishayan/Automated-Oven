import json
import time
from random import randint
from datetime import datetime
from asyncio import sleep
from DB import DB


class Users(DB):
    def __init__(self, e, dbPath='./db/UsersDB.json'):
        super().__init__(dbPath)
        self.e = e
        self.lastUpdatedValueNow = 0

    async def add(self, entry):
        try:
            date = datetime.now().strftime("%Y-%m-%d")
            if date not in self.db:
                self.db[date] = {}
            self.db[date][str(time.time()).split('.')[0]] = int(entry)
        except Exception as e:
            print(e)

    async def getAll(self, date=""):
        if len(date) > 0:
            try:
                return self.db[date]
            except:
                return self.db
        return self.db

    async def logEnergy(self):
        interval = 3
        while not self.e._SIGKILL:
            aggregate = []
            for _ in range(interval):
                aggregate.append(await self.detect())
                await sleep(interval)

            self.lastUpdatedValueNow = round(sum(aggregate)/interval)

            await self.add(self.lastUpdatedValueNow/(3600/interval))

    async def detect(self):
        base = 15
        if self.e.cook.topRod.pin.value:
            base += 325
        return base

    async def getNow(self):
        return self.lastUpdatedValueNow

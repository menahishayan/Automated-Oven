import json
import time
from random import randint
from datetime import datetime
from asyncio import sleep


class Energy:
    def __init__(self, dbPath='./EnergyDB.json'):
        self.path = dbPath

    async def add(self, entry):
        try:
            f = open(self.path).read()
            db = json.loads(f)
            date = datetime.now().strftime("%Y-%m-%d")
            if date not in db:
                db[date] = {}
            db[date][str(time.time()).split('.')[0]] = int(entry)
            with open(self.path, "w") as outfile:
                json.dump(db, outfile)
        except Exception as e:
            print(e)

    async def getAll(self, date=""):
        f = open(self.path).read()
        db = json.loads(f)
        if len(date) > 0:
            try:
                return db[date]
            except:
                return db
        return db

    async def logEnergy(self):
        while True:
            await self.add(await self.getNow())
            await sleep(20)

    async def getNow(self):
        return randint(0, 350)

    def __str__(self):
        return self.getAll()

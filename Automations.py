import json

class Automations:
    def __init__(self, dbPath='./db/AutomationsDB.json'):
        self.path = dbPath

    async def add(self, entry):
        f = open(self.path).read()
        db = json.loads(f)
        db.append(entry)
        f.close()
        with open(self.path, "w") as outfile: 
            json.dump(db, outfile)

    async def get(self):
        f = open(self.path).read()
        db = json.loads(f)
        return db

    def __str__(self):
        return self.get()
        
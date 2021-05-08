import json
import time

class Energy:
    def __init__(self, dbPath='./EnergyDB.json'):
        self.path = dbPath

    def add(self, entry):
        f = open(self.path).read()
        db = json.loads(f)
        db[time.time()] = int(entry)
        f.close()
        with open(self.path, "w") as outfile: 
            json.dump(db, outfile)

    def get(self, date=""):
        f = open(self.path).read()
        db = json.loads(f)
        if len(date) > 0:
            try:
                return db[date]
            except:
                return db
        return db

    def __str__(self):
        return self.get()
        
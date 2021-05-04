import json

class History:
    def __init__(self, dbPath='./HistoryDB.json'):
        self.path = dbPath

    def add(self, entry):
        f = open(self.path).read()
        db = json.loads(f)
        db.append(entry)
        f.close()
        with open(self.path, "w") as outfile: 
            json.dump(db, outfile)

    def get(self):
        f = open(self.path).read()
        db = json.loads(f)
        return db

    def __str__(self):
        return self.get()
        
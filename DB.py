import json

class DB:
    def __init__(self, dbPath):
        self.path = dbPath
        f = open(self.path).read()
        self.db = json.loads(f)

    def __del__(self):
        with open(self.path, "w") as outfile: 
            json.dump(self.db, outfile)

    def set(self,k,v):
        self.db[k] = v

    def push(self,item):
        self.db.append(item)

    def get(self):
        return self.db
        
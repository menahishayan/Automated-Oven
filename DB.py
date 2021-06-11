import json

class DB:
    def __init__(self, dbPath,readOnly=False):
        self.path = dbPath
        f = open(self.path).read()
        self.db = json.loads(f)

    def flush(self):
        with open(self.path, "w") as outfile: 
            json.dump(self.db, outfile)

    def set(self,k,v):
        self.db[k] = v
        self.flush()

    def push(self,item):
        self.db.append(item)
        self.flush()

    async def get(self,item=None):
        if item and item in self.db:
            return self.db[item]
        return self.db

    def _get(self,item=None):
        if item and item in self.db:
            return self.db[item]
        return self.db
        
    def has(self,item):
        return item in self.db
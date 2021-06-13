import json
from time import process_time
class DB:
    def __init__(self, dbPath):
        self.path = dbPath
        with open(self.path, "r+") as f: 
            self.db = json.loads(f.read())

    def flush(self):
        interval = 60
        t = round(process_time())
        try:
            if t % interval < 15 or t%interval >interval-15:
                with open(self.path, "w") as outfile: 
                    json.dump(self.db, outfile)
        except Exception as e:
            print(e)

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
        if item:
            if item in self.db:
                return self.db[item]
            else:
                return None
        else:
            return self.db
        
    def has(self,item):
        return item in self.db
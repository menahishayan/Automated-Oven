from time import time
from DB import DB


class Users(DB):
    def __init__(self, e, dbPath='./db/UsersDB.json'):
        super().__init__(dbPath)
        self.e = e
        self.currentUsers = set()

    async def add(self, name):
        try:
            self.currentUsers.add(name)
            self.set(str(round(time())), list(self.currentUsers))
            self.e.log(self.db)
        except Exception as e:
            self.e.err(e)

    async def get(self):
        return list(self.currentUsers)

from time import time
from DB import DB


class Users(DB):
    def __init__(self, e, dbPath='./db/UsersDB.json'):
        super().__init__(dbPath)
        self.e = e
        self.currentUsers = set()

    async def add(self, name):
        try:
            self.e.log(name)
            self.currentUsers.add(name)
            self.e.log(self.currentUsers)

            self.set(str(round(time())), list(self.currentUsers))
        except Exception as e:
            self.e.err(e)

    async def get(self):
        return list(self.currentUsers)

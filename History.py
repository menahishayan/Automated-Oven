from time import time
from DB import DB


class History(DB):
    def __init__(self, e, dbPath='./db/HistoryDB.json'):
        super().__init__(dbPath)
        self.e = e

    async def add(self, name, steps, temp, duration):
        try:
            if not name or name == 'Empty':
                name = '{} for {} min'.format(temp, duration)

            startTime = steps[0]['startTime']
            steps = steps.copy()
            for s in steps:
                if 'startTime' in s:
                    del s['startTime']
                if 'endTime' in s:
                    del s['endTime']
                if 'pauseTime' in s:
                    del s['pauseTime']

            playbackHistory = {
                'timestamp': startTime,
                'users': await self.e.users.get()
            }
            if self.has(name) and len(self.db[name]['steps']) == len(steps):
                timestamps = [p['timestamp'] for p in self.db[name]['playbackHistory']]
                if startTime not in timestamps:
                    self.db[name]['playbackHistory'].append(playbackHistory)
            else:
                self.db[name] = {
                    'playbackHistory': [playbackHistory],
                    'steps': steps
                }
            self.flush()

        except Exception as e:
            self.e.err(e)

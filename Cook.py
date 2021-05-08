from pandas import read_csv

__version__ = '0.6.0'

class Cook:
    def __init__(self,e):
        self.default = {
            'top': 180,
            'bottom': 180,
            'time': 20,
            'cooktype': 'Cook',
        }
        self.e = e

    async def init(self, method='fixed'):
        if method=='fixed':
            self.df = read_csv('Temp.csv', index_col=0)
        # derived 

    def start(self, item):
        try:
            top = self.df['Top'][item]
            bottom = self.df['Bottom'][item]
            time = self.df['Time'][item]
            cooktype = self.df['Type'][item]

            # self.rods.setTop(top)
            # self.rods.setBottom(bottom)

        except Exception as e:
            self.e.err("Cook - Unknown Food")
            self.e.err(e)
            return 180,180,20,'Cook'

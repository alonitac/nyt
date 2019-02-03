import pandas as pd
import pymongo
import requests


class APIclient(object):

    def __init__(self):
        self.db_name = 'nty_archive'
        self.base_url = 'https://api.nytimes.com/svc/archive/v1/{}/{}.json?api-key={}'

        with open('apikey') as f:
            key = f.read()

        self.key = key
        self.dbclient = pymongo.MongoClient()

    def _cursor_to_pandas(self, cursor):
        return pd.DataFrame(list(cursor))

    def push_archive(self, year, month):
        url = self.base_url.format(year, month, self.key)
        data = requests.get(url).json()
        for item in data['response']['docs']:
            r = self.dbclient[self.db_name][str(year)][str(month)].insert_one(item).inserted_id
            print(r)

    def fetch_archive(self):
        pass


if __name__ == '__main__':
    api_client = APIclient()
    api_client.push_archive(2019, 1)

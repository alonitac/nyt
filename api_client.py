import pandas as pd
import pymongo
import requests
from pymongo.errors import DuplicateKeyError
import json
import dateutil.parser


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
        summary = {
            'inserted': [],
            'duplication': []
        }
        for item in data['response']['docs']:
            try:
                r = self.dbclient[self.db_name][str(year)][str(month)].insert_one(item).inserted_id
                summary['inserted'].append(r)
            except DuplicateKeyError as e:
                summary['duplication'].append(str(e)[85: -3])

        return summary

    def fetch_archive(self):
        self.dbclient[self.db_name].find()

    def get_data_from_api(self, y_from, y_to, m_from=1, m_to=12):
        years = range(y_from, y_to+1)
        months = range(m_from, m_to+1)
        for y in years:
            for m in months:
                summary = api_client.push_archive(y, m)
                with open('data/duplications/{}_{}.json'.format(y, m), 'w') as fp:
                    json.dump(summary, fp)

    def drop_collection(self, col):
        res = self.dbclient[self.db_name][col].drop()
        print(res)


if __name__ == '__main__':
    api_client = APIclient()

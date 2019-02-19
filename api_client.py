import pandas as pd
import pymongo
import requests
from os.path import dirname, join
from pymongo.errors import DuplicateKeyError
import json
import dateutil.parser


class APIclient(object):

    def __init__(self):
        self.db_name = 'nty_archive'
        self.collection = 'data'
        self.base_url = 'https://api.nytimes.com/svc/archive/v1/{}/{}.json?api-key={}'

        with open(join(dirname(__file__), 'apikey')) as f:
            key = f.read()

        self.key = key
        self.dbclient = pymongo.MongoClient()

    def push(self, year, month):
        url = self.base_url.format(year, month, self.key)
        data = requests.get(url).json()
        summary = {
            'inserted': [],
            'duplication': []
        }
        for item in data['response']['docs']:
            try:
                item['pub_date'] = dateutil.parser.parse(item['pub_date'])
                r = self.dbclient[self.db_name][self.collection].insert_one(item).inserted_id
                summary['inserted'].append(r)
            except DuplicateKeyError as e:
                summary['duplication'].append(str(e)[85: -3])

        return summary

    def fetch(self, query, projections):
        res = self.dbclient[self.db_name][self.collection].find(query, projections)
        return pd.DataFrame(list(res))

    def get_data_from_api(self, y_from, y_to, m_from=1, m_to=12):
        years = range(y_from, y_to+1)
        months = range(m_from, m_to+1)
        for y in years:
            for m in months:
                summary = self.push(y, m)
                with open('data/duplications/{}_{}.json'.format(y, m), 'w') as fp:
                    json.dump(summary, fp)

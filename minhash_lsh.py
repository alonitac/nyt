import itertools
from lsh import cache, minhash  # https://github.com/mattilyra/lsh
import datetime
from api_client import APIclient
import pandas as pd
import community
import networkx as nx


class MinHashLSH(object):
    def __init__(self, char_ngram=4, bands=20, seeds=100, jaccard_min=0.7, jaccard_max=0.9):
        self.char_ngram = char_ngram
        self.bands = bands
        self.seeds = seeds
        self.jaccard_range = (jaccard_min, jaccard_max)
        self.api_client = APIclient()

    def generate_shingles(self, text):
        return set(text[head:head + self.char_ngram] for head in range(0, len(text) - self.char_ngram))

    def jaccard(self, set_a, set_b):
        intersection = set_a & set_b
        union = set_a | set_b
        return len(intersection) / len(union)

    def get_data(self, start_year, end_year):
        res = self.api_client.aggregate(
            [
                {'$match': {'pub_date': {'$lte': datetime.datetime(end_year, 12, 31),
                                         '$gte': datetime.datetime(start_year, 1, 1)}}},
                {
                    '$project':
                        {
                            'headline': '$headline.main',
                            'snippet': '$snippet',
                            'by': {'$substr': ['$byline.original', 3, -1]},
                        }
                }
            ]
        )

        df = pd.DataFrame(list(res))
        df['text'] = df['by'] + ' ' + df['headline'] + ' ' + df['snippet']
        df = df[['_id', 'text']]
        df = df.set_index('_id')
        return df

    def get_candidate_pairs(self, df):
        hasher = minhash.MinHasher(seeds=self.seeds, char_ngram=self.char_ngram, hashbytes=4)
        lshcache = cache.Cache(num_bands=self.bands, hasher=hasher)
        df['fingerprint'] = df['text'].apply(lambda t: hasher.fingerprint(t.encode('utf8')))
        df.apply(lambda f: lshcache.add_fingerprint(f['fingerprint'], doc_id=f.name), axis=1)

        candidate_pairs = set()
        for b in lshcache.bins:
            for bucket_id in b:
                if len(b[bucket_id]) > 1:
                    pairs_ = set(itertools.combinations(b[bucket_id], r=2))
                    candidate_pairs.update(pairs_)
        return candidate_pairs

    def get_stories_details(self, comm):
        stories = []
        for c in comm:
            res = self.api_client.aggregate(
                [
                    {'$match': {'_id': {'$in': c}}},
                    {
                        '$project':
                            {
                                'pub_date': '$pub_date',
                                'headline': '$headline.main',
                                'by': {'$substr': ['$byline.original', 3, -1]},
                                'url': '$web_url',
                                # 'image': {'$first': 'multimedia'}
                            }
                    },
                    {'$sort': {'pub_date': 1}}
                ]
            )
            stories.append(pd.DataFrame(list(res)))
        return stories

    def get_similar_stories(self, start_year, end_year):
        df = self.get_data(start_year, end_year)
        candidate_pairs = self.get_candidate_pairs(df)
        comm = self.find_community(df, candidate_pairs)
        stories = self.get_stories_details(comm)
        return stories

    def find_community(self, df, candidate_pairs):
        G = nx.Graph()
        # similarities = []
        for docid_a, docid_b in candidate_pairs:
            shingles_a = self.generate_shingles(df.loc[docid_a]['text'])
            shingles_b = self.generate_shingles(df.loc[docid_b]['text'])
            jaccard_sim = self.jaccard(shingles_a, shingles_b)
            if self.jaccard_range[0] <= jaccard_sim <= self.jaccard_range[1]:
                G.add_edge(docid_a, docid_b, weight=jaccard_sim)
                # similarities.append((docid_a, docid_b, jaccard_sim))
        partition = community.best_partition(G)
        comm = []
        for com in set(partition.values()):
            comm.append([nodes for nodes in partition.keys() if partition[nodes] == com])
        return comm

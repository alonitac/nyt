import itertools
from lsh import cache, minhash  # https://github.com/mattilyra/lsh
import datetime
from api_client import APIclient
import pandas as pd
import community
import networkx as nx


class MinHashLSH(object):
    def __init__(self, char_ngram=4, bands=20, seeds=100, jaccard_min=0.7, jaccard_max=0.95):
        self.char_ngram = char_ngram
        self.bands = bands
        self.seeds = seeds
        self.jaccard_range = (jaccard_min, jaccard_max)
        self.api_client = APIclient()

    def _generate_shingles(self, text):
        return set(text[head:head + self.char_ngram] for head in range(0, len(text) - self.char_ngram))

    def _jaccard(self, set_a, set_b):
        intersection = set_a & set_b
        union = set_a | set_b
        return len(intersection) / len(union)

    def _get_data(self, start_year, end_year):
        res = self.api_client.aggregate(
            [
                {'$match': {'pub_date': {'$lte': datetime.datetime(end_year, 12, 31),
                                         '$gte': datetime.datetime(start_year, 1, 1)}}},
                {
                    '$project':
                        {
                            'headline': '$headline.main',
                            'snippet': '$snippet',
                            # 'by': {'$substr': ['$byline.original', 3, -1]},
                        }
                }
            ]
        )

        df = pd.DataFrame(list(res)).dropna()
        df['text'] = df['headline'].astype(str) + ' ' + df['snippet'].astype(str)
        df['text'] = df['text'].apply(lambda x: x.encode('utf8'))
        df = df[['_id', 'text']]
        df = df.set_index('_id')
        return df

    def _get_stories_details(self, comm):
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
                                'url': '$web_url',
                            }
                    },
                    {'$sort': {'pub_date': 1}}
                ]
            )
            story = pd.DataFrame(list(res))

            # if story has last less then 1 day, it isn't a story
            if (story.iloc[-1]['pub_date'] - story.iloc[0]['pub_date']).days > 1:
                stories.append(story)
        return stories

    def get_similar_stories(self, start_year, end_year):
        df = self._get_data(start_year, end_year)
        candidate_pairs = self._get_candidate_pairs(df)
        comm = self.find_community(df, candidate_pairs)
        stories = self._get_stories_details(comm)
        return stories

    def _get_candidate_pairs(self, df):
        hasher = minhash.MinHasher(seeds=self.seeds, char_ngram=self.char_ngram, hashbytes=4)
        lshcache = cache.Cache(num_bands=self.bands, hasher=hasher)
        df['fingerprint'] = df['text'].apply(lambda t: hasher.fingerprint(t))
        df.apply(lambda f: lshcache.add_fingerprint(f['fingerprint'], doc_id=f.name), axis=1)

        communities = []
        candidate_pairs = set()
        for b in lshcache.bins:
            for bucket_id in b:
                if len(b[bucket_id]) > 1:
                    pairs = set(itertools.combinations(b[bucket_id], r=2))
                    # communities.append(self.find_community(df, pairs))
                    candidate_pairs.update(pairs)
        return candidate_pairs

    def find_community(self, df, candidate_pairs):
        G = nx.Graph()
        # similarities = []
        for docid_a, docid_b in candidate_pairs:
            shingles_a = self._generate_shingles(df.loc[docid_a]['text'])
            shingles_b = self._generate_shingles(df.loc[docid_b]['text'])
            jaccard_sim = self._jaccard(shingles_a, shingles_b)
            if self.jaccard_range[0] <= jaccard_sim <= self.jaccard_range[1]:
                G.add_edge(docid_a, docid_b, weight=jaccard_sim)
                # similarities.append((docid_a, docid_b, jaccard_sim))
        partition = community.best_partition(G)
        comm = []
        for com in set(partition.values()):
            comm.append([nodes for nodes in partition.keys() if partition[nodes] == com])
        return comm

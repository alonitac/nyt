import itertools
from lsh import minhash  # https://github.com/mattilyra/lsh
import datetime
from api_client import APIclient
import pandas as pd
import community
import networkx as nx
import numpy as np
from collections import defaultdict
import pickle

char_ngram = 4
bands = 20
seeds = 100
jaccard_min = 0.7
jaccard_max = 0.95
api_client = APIclient()

hasher = minhash.MinHasher(seeds=seeds, char_ngram=char_ngram, hashbytes=4)

def generate_shingles(text):
    return set(text[head:head + char_ngram] for head in range(0, len(text) - char_ngram))

def jaccard(set_a, set_b):
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union)

def clean_text(df):
    df['text'] = df['headline'].astype(str) + ' ' + df['snippet'].astype(str)
    df['text'] = df['text'].apply(lambda x: x.encode('utf8'))
    df = df[['_id', 'text']]
    df = df.set_index('_id')
    return df

def get_text_by_id(id):
    res = api_client.aggregate(
            [
                {'$match': {'_id': id}},
                {'$project': {'headline': '$headline.main', 'snippet': '$snippet'}}
            ]
        )
    return clean_text(pd.DataFrame(list(res)))

with open('bins/tot_bins.pkl', 'rb') as f:
    tot_bins = pickle.load(f)


candidate_pairs = set()
for b in tot_bins:
    for bucket_id in b:
        if len(b[bucket_id]) > 1:
            pairs = set(itertools.combinations(b[bucket_id], r=2))
            candidate_pairs.update(pairs)

G = nx.Graph()
for docid_a, docid_b in candidate_pairs:
    shingles_a = generate_shingles(get_text_by_id(docid_a).iloc[0]['text'])
    shingles_b = generate_shingles(get_text_by_id(docid_b).iloc[0]['text'])
    print(get_text_by_id(docid_a).iloc[0], get_text_by_id(docid_b).iloc[0])
    jaccard_sim = jaccard(shingles_a, shingles_b)
    if jaccard_min <= jaccard_sim <= jaccard_max:
        G.add_edge(docid_a, docid_b, weight=jaccard_sim)
partition = community.best_partition(G)
comm = []
for com in set(partition.values()):
    comm.append([nodes for nodes in partition.keys() if partition[nodes] == com])

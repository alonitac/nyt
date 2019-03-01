import datetime
from api_client import APIclient
import pandas as pd
from nltk import ngrams
import numpy as np
from utils import next_prime

#############################
# get the data from mongoDB #
#############################

api_client = APIclient()
res = api_client.aggregate(
    [
        {'$match': {'pub_date': {'$lte': datetime.datetime(2018, 12, 31),
                    '$gte': datetime.datetime(2018, 1, 1)}}},
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

##############
# Shinglings #
##############

df = pd.DataFrame(list(res))
n = 2
df['ngrams'] = (df['by'] + ' ' + df['headline'] + ' ' + df['snippet']).apply(lambda s: [x for x in ngrams(s.split(), n)])
df = df[['_id', 'ngrams']]
df = df.set_index('_id')

shingles = {}
shingles_num = 0


def map_shingles(sh_lst):
    global shingles_num
    tmp = set()
    for r in sh_lst:
        if not shingles.get(r):
            shingles[r] = shingles_num
            shingles_num += 1
            tmp.add(shingles_num)
    return np.array(tmp)


###############
# Min Hashing #
###############

num_permutation = 100
df['ngrams'] = df['ngrams'].apply(map_shingles)
tmp = np.arange(num_permutation)
np.random.shuffle(tmp)
coeff_a = tmp[:num_permutation]
np.random.shuffle(tmp)
coeff_b = tmp[:num_permutation]
prime = next_prime(shingles_num)


def row_hashing(ng_idx, hash_func):
    min = np.inf
    for j in ng_idx:
        if hash_func(j) < min:
            min = hash_func(j)
    return min


def generate_hash_func(i):
    def hash(x):
        return ((coeff_a[i] * x + coeff_b[i]) % prime) % shingles_num

    return hash


for i in range(num_permutation):
    df[i] = df['ngrams'].apply(lambda ng_idx: row_hashing(ng_idx, generate_hash_func(i)))


##############################
# Locality-Sensitive Hashing #
##############################

band_num = 20
rows_per_band = 5
bucket_num = 1000


def jaccard_sim(x, y):
    intersection = len(list(set(x).intersection(y)))
    union = (len(x) + len(y)) - intersection
    return float(intersection / union)


s = 0.6
for i in range(len(df)):
    for j in range(i+1, len(df)):
        if jaccard_sim(df.iloc[i][1:], df.iloc[j][1:]) >= s:
            print('pairs: {} and {}'.format(df.index.values[i], df.index.values[j]))

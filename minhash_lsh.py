import itertools
import lsh
# https://github.com/mattilyra/lsh


# a pure python shingling function that will be used in comparing
# LSH to true Jaccard similarities
def shingles(text, char_ngram=5):
    return set(text[head:head + char_ngram] for head in range(0, len(text) - char_ngram))


def jaccard(set_a, set_b):
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union)


def candidate_duplicates(document_feed, char_ngram=5, seeds=100, bands=5, hashbytes=4):
    char_ngram = 5
    sims = []
    hasher = minhash.MinHasher(seeds=seeds, char_ngram=char_ngram, hashbytes=hashbytes)
    if seeds % bands != 0:
        raise ValueError('Seeds has to be a multiple of bands. {} % {} != 0'.format(seeds, bands))

    lshcache = cache.Cache(num_bands=bands, hasher=hasher)
    for line in document_feed:
        line = line.decode('utf8')
        docid, headline_text = line.split('\t', 1)
        fingerprint = hasher.fingerprint(headline_text.encode('utf8'))

        # in addition to storing the fingerpring store the line
        # number and document ID to help analysis later on
        lshcache.add_fingerprint(fingerprint, doc_id=docid)

    candidate_pairs = set()
    for b in lshcache.bins:
        for bucket_id in b:
            if len(b[bucket_id]) > 1:
                pairs_ = set(itertools.combinations(b[bucket_id], r=2))
                candidate_pairs.update(pairs_)

    return candidate_pairs
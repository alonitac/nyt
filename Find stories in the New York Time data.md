# Find *stories* in the New York Time data

### Motivation

The NYT archive contains a few millions of documents including articles, videos, blogs etc. Naturally, a collection of documents can be interpreted as a *story*, which mean a sequence of publications in a time frame that shares the same subject and draws to the reader some logical story. For example: TBD

We would like to automatically detect stories over 30 year of data, visualize it interactively in a time-line so we could explore conveniently over stories and try to find some non obvious stories.

### The Method

As long as finding stories may be difficult problem even on the semantic level, we simplified it with a very naive assumption: documents that belongs to same story have similar title or lead paragraph. 

The task was divided into 4 sections: 

1. Finding <u>pairs of similar documents</u> that can be considered as good candidates. 
2. <u>Finding community</u> of documents that are similar to each other.
3. Visualize it.
4. Randomly sample generated stories and manually evaluate if they are indeed stories according to the definition.

### Similar items using minhash and LSH

Each document has represented by it's title and lead paragraph (just as a long sentence), and we applied the <u>similar items algorithm</u> with **a modification**: the sentences themselves were minhashed instead their shingle index.

why is that? the whole data was 1.83 GB with 2131065 documents, what caused the main memory to overload very quickly if we tried to process the data in one piece. So for minhashing we partitioned the processing to pieces by **years of publication**, and saves everything in pickles files. All in all the process took ~1 hour of running time. Now, let's say that first we would shingles to 4-grams and only then do the minhashing, as we taught in class, then when we would like to evaluate performance for 5-grams for example, we would need to minhash again which means one more hour of processing time. 

So by minhash the sentences themselves gain minhashing the whole data only once.

#### Parameters choosing - n-grams, k (permutations), # bands. 

We choose parameters by evaluating results of one year of data, 2018.

 As for **number of permutations k**, we started with k=100. We took pair of similar sentences and saw that changing to k=1000 reduce the variance of Jaccard estimation only in a negligible value, so we stay with **k=100**.  

As for n-gram, because of the fact that we evaluate results manually by observing the generated stories, we couldn't perform kind of model selection for choosing ideal n-grams, but only to evaluate it by feeling. We tried n-grams of words and characters with n=2, 3, 4. Finally, **4-grams of characters** was produces satisfied results. 

As for number of bands, since we have k=100 we tried 5 different probabilities model characteristics as follows:

 ![](/home/alon/projects/nyt/jac.png)

We bear in mind the documents of a story may not be that similar, but with some differences, so we wanted out model to be relaxed. We choose **# bands=20** (the red line).

The process ended up with a list of 21993216 (~22M!) candidate pairs. Since we didn't want pairs with Jaccard of 1, which mean equal documents (although we drop duplicates), we passed pairs with **0.7 <= Jaccard <= 0.9**.

### Find Communities

We defined a weighted graph in which each edge is a candidates and the weight is Jaccard similarity. We use the `community` python library and performed Louvain algorithm to find best partition, i.e the highest partition of the dendrogram.

### Results


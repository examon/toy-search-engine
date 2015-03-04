## Toy Search Engine

This is my simple toy search engine. I do not expect to grow this into anything
serious, just wanted to try some simple Boolean retrieval.


## Example

Start the engine by specifying source directory where are the data you want to index.

    $ python3 toy-search-engine.py shakespeare
    Documents extracted in: 14.821529 ms
    Document tables built in: 1.006842 ms
    Number of source documents: 43
    Total corpus size: 5.095254 MB
    Tokenizing...
    Tokenizer finished after: 10854.145527 ms
    Indexing...
    Index built in: 1378.195286 ms
    Number of indexed terms: 19889
    Avg number of elements in incidence list: 5
    Avg length of indexed term: 7

Then run the query. Currently only Boolean retrieval with binary AND, OR and !(negation operator):

    query> caesar
    shakespeare/othello
    shakespeare/antonyandcleopatra
    shakespeare/measureforemeasure
    shakespeare/1kinghenryvi
    shakespeare/3kinghenryvi
    shakespeare/kingrichardiii
    shakespeare/kinghenryv
    shakespeare/2kinghenryvi
    shakespeare/juliuscaesar
    shakespeare/allswellthatendswell
    shakespeare/cymbeline
    11 results. Query executed in: 2.245665 ms

    query> romeo AND juliet
    shakespeare/romeoandjuliet
    1 results. Query executed in: 35.736322 ms

    query> hamlet OR cleopatra
    shakespeare/hamlet
    shakespeare/antonyandcleopatra
    shakespeare/romeoandjuliet
    3 results. Query executed in: 1.028538 ms

    query> hamlet OR cleopatra AND !romeo
    shakespeare/hamlet
    shakespeare/antonyandcleopatra
    2 results. Query executed in: 1.818657 ms

To quit the prompt:

    query>:q

To save the index to the file called index.txt:

    query>:save index.txt

To print index data structure to the stdout (this can take a while):

    query>:index

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (C) 2015 Tomas Meszaros <exo [at] tty [dot] sk>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


""" Just a simple toy search engine.
"""

import os
import sys
import time
import pprint

# OPTIONAL: enable for static analysis, you will need obiwan package
#from obiwan import *; install_obiwan_runtime_check()

# CONFIG
MIN_TERM_LENGTH = 2  # don't index terms shorter than MIN_TERM_LENGTH chars
MAX_TERM_LENGTH = 20 # don't index terms longer than MAX_TERM_LENGTH chars


def timeit(message: str):
    """
    Named decorator "@timeit". Times execution of the decorated function
    in milliseconds. Prints the @message + measured time.

    Note: the is some overhead from the function calls so the measured time is
    not strictly 100% correct (but is good enough).
    """
    def timer(func):
        """ Default decorator @timer.
        """
        def inner(*args, **kwargs):
            """ This is where the measurement happens.
            """
            start = time.time()
            result = func(*args, **kwargs)
            end = time.time()
            total_milliseconds = (end - start) * 1000
            print("%s %.1f ms" % (message, total_milliseconds))
            return result
        return inner
    return timer


class Collector(object):
    """
    Extracts plaintext from the given documents. Plaintext is stored along with
    some additional data and statistics.

    @self.__library: {str: str}, e.g. {"/path/doc1.txt": "doc1 content...", ...}
    @self.__doc_id_table: dict, e.g. {"/path/doc1.txt": 1, ...}
    @self.__doc_path_table: dict, e.g. {1: "/path/doc1.txt", ...}
    @self.__curr_doc_id: int
    @self.__dir_path: str, e.g. "/home/joe/mydocuments"
    """
    def __init__(self, dir_path: str):
        """ dir_path should look like "/home/joe/Documents"
        """
        self.__library = {}
        self.__doc_id_table = {}
        self.__doc_path_table = {}
        self.__curr_doc_id = 1 # currently available document id
        self.__dir_path = dir_path

        self.__extract_documents()
        self.__build_document_tables()

    @timeit("Documents extracted in:")
    def __extract_documents(self):
        """
        Extracts paint text data from files from the @self.__dir_path and saves
        extracted text into the @self.__library.

        Sanitize your files before opening them, or you will get
        UnicodeDecodeError exception. Use the following command from shell:

        $ iconv -f utf-8 -t utf-8 -c file.txt
        """
        try:
            directory = os.listdir(self.__dir_path)
        except NotADirectoryError as error:
            print(error)
            exit(1)
        except FileNotFoundError as error:
            print(error)
            exit(1)

        for file_name in directory:
            file_path = self.__dir_path + '/' + file_name
            if not os.path.isfile(file_path):
                continue
            with open(file_path, 'r') as file_handler:
                try:
                    self.__library[file_path] = file_handler.read()
                except UnicodeDecodeError as error:
                    print(error)
                    print("Sanitize your data so they are in the UTF-8, use:")
                    print("$ iconv -f utf-8 -t utf-8 -c file.txt")
                    exit(1)

    def __build_document_tables(self):
        """ Constructs __doc_id_table and __doc_path_table.
        """
        for doc in self.__library.keys():
            self.__doc_id_table[doc] = self.__curr_doc_id
            self.__doc_path_table[self.__curr_doc_id] = doc
            self.__curr_doc_id += 1

    def yield_doc_paths(self) -> str():
        """ Yields document path as a string, e.g. "/home/joe/doc.txt".
        """
        for doc in self.__library.keys():
            yield doc

    def get_doc_id(self, doc_path: str) -> int:
        """ Returns document id for the given document name.
        """
        return self.__doc_id_table[doc_path]

    def get_doc_id_list(self) -> [int]:
        """ Returns all document IDs.
        """
        return list(self.__doc_path_table.keys())

    def get_doc_path(self, doc_id: int) -> str:
        """ Returns document path for given document id.
        """
        return self.__doc_path_table[doc_id]

    def get_doc_content(self, doc_path: str) -> str:
        """ Returns document content located at doc_path.
        """
        # TODO possibly KeyError
        return self.__library[doc_path]

    def print_documents_stats(self):
        """ Prints basic stats about the documents owned by the Collector.
        """
        print("Number of source documents: %s" % len(self.__library))
        library_size = 0
        for source_file in os.listdir(self.__dir_path):
            file_path = self.__dir_path + '/' + source_file
            if os.path.isfile(file_path):
                library_size += os.path.getsize(file_path)
        print("Total corpus size: %.2f MB" % (library_size / 1024 / 1024))


class Tokenizer(object):
    # TODO: too few methods?
    """
    Takes care of tokenizing plain text.

    @self.__document: str, document in plain text
    """

    def __init__(self, document: str):
        """ Document should be plain test and in UTF-8.
        """
        self.__document = document

    def yield_tokens(self) -> str():
        """ Tokenizes self.__document and yields those tokens.
        """
        for token in self.__document.split():
            if not token.isalnum():
                continue
            # tokens of length <3 and >20 are irrelevant for our use
            if len(token) < MIN_TERM_LENGTH or len(token) > MAX_TERM_LENGTH:
                continue
            yield token.lower()

class Indexer:
    """
    Takes list of tokens and builds index.

    @self.__index: {"term": [file_id1, file_id2, ...], ...}

                      e.g.

                   {'a': [1, 2, 3, 4],
                    'accessible': [1],
                    'all': [1], ...}

    @self.__keywords: {str: function, ...}, This table holds mappings from
    the available keywords user can use in the query to functions that will
    be executed. E.g. when query contains "he OR she" function set.union will
    be carried on left ("he") and right ("she") term of the query.

    """
    def __init__(self, source_dir: str):
        """
        @source_folder is the source directory for the data that are used
        during the index construction.
        """
        self.__index = {}
        self.__keywords = {"AND": set.intersection, "OR": set.union}

        self.__collector = Collector(source_dir)
        self.__collector.print_documents_stats()
        self.__token_id_list = self.__tokenize()
        self.__token_id_list.sort(key=lambda x: x[0])
        self.__make_index()
        self.index_stats()

    @timeit("Tokenizer finished after:")
    def __tokenize(self):
        """ Tokenizes data from collector and returns them as:

        @token_id_list looks like this:
        [('a', 1), ('a', 2), ('all', 1), ('an', 3), ...]
        """
        print("Tokenizing...")
        token_id_list = []
        for doc_path in self.__collector.yield_doc_paths():
            doc_id = self.__collector.get_doc_id(doc_path)
            doc_content = self.__collector.get_doc_content(doc_path)
            tokenizer = Tokenizer(doc_content)
            for token in tokenizer.yield_tokens():
                token_id_pair = (token, doc_id)
                token_id_list.append(token_id_pair)
        return token_id_list

    @timeit("Index built in:")
    def __make_index(self):
        """
        We are building index from the list of tuples. Each tuple contains one
        token and the document ID where is this token located.
        """
        print("Indexing...")
        for pair in self.__token_id_list:
            token = pair[0]
            doc_id = pair[1]
            if token not in self.__index:
                self.__index[token] = [doc_id]
            else:
                if not doc_id in self.__index[token]:
                    self.__index[token].append(doc_id)

    def __get_postings(self, key: str) -> [int]:
        """ For given key, returns reference to the corresponding posting lists.
        """
        try:
            return self.__index[key]
        except KeyError:
            print("error: no entry for %s." % key)
            return []

    def __parse_query(self, query: str) -> list:
        """
        Returns posting list satisfing query or empty list on error.

        @query: e.g "cat AND hores OR table"
        """
        query = query.split()

        if len(query) % 2 == 0:
            # query = ["str1", "str2"] is invalid
            print("invalid query: specify set operation")
            print("example: brutus AND caesar")
            return []

        for idx, value in enumerate(query):
            if idx % 2 == 1:
                # Replace keyword with function that will perform
                # adequate operations on postings list.
                # E.g. "OR" -> set.union()
                if value not in self.__keywords and len(query) > 1:
                    print("invalid query: some keyword from %s should be "
                          "betweeen query terms" % self.__keywords.keys())
                    return []
                else:
                    query[idx] = self.__keywords[value]
            else:
                # Replace query term with posting list for each query term.
                try:
                    if value.startswith('!'):
                        # Here we implement negation of the term. Example:
                        # Query "you AND !he" asks for all documents where
                        # "you" is present and "he" is not.

                        # Negation for "!he" is done by fetching posting list
                        # for term "he". After, we make set difference against
                        # all ID in the Collectors database and so we get set
                        # of documents IDs where is not "he" present.
                        postings = set(self.__get_postings(value[1:]))
                        all_doc_id = set(self.__collector.get_doc_id_list())
                        difference = list(set.difference(all_doc_id, postings))
                        query[idx] = difference
                    else:
                        query[idx] = self.__get_postings(value)
                except KeyError:
                    query[idx] = []
        return query

    def __merge(self, query: list) -> [int]:
        """
        Merges @query = [[1,2,3,4], "AND", [2,3,4], "OR, [1,2]]
        into relevant docIDs: [1,2,3,4].
        """
        if query is None:
            return []
        while len(query) > 0:
            if len(query) == 1:
                return query[0]
            first = set(query[0])
            function = query[1] # some set function from self.__keywords values
            second = set(query[2])
            tmp = [list(function(first, second))]
            tmp.extend(query[3:])
            query = tmp
        return query

    def yield_search_result(self, query: str) -> str():
        """ Yields result of the search given by the presented query.
        """
        parsed = self.__parse_query(query)
        for i in self.__merge(parsed):
            yield self.__collector.get_doc_path(i)

    @property
    def index(self):
        """ Returns reference to the index.
        """
        return self.__index

    def index_stats(self):
        """ Prints bunch of stats about the index.
        """
        print("Number of indexed terms: %d" % len(self.__index))
        avg_term_occurences = sum([len(i) for i in self.__index.values()]) \
                              / len(self.__index)
        print("Avg number of elements in incidence list: %d" \
               % avg_term_occurences)
        avg_term_length = sum([len(i) for i in self.__index.keys()]) \
                          / len(self.__index)
        print("Avg length of indexed term: %d" % avg_term_length)

    def save_index(self, destination: str):
        """ Saves index to the files located at @destination.
        """
        with open(destination, "w") as index_file:
            for key in self.__index:
                index_file.write("%s : %s\n" % (key, self.__index[key]))


class Client(object):
    """
    Provides user interface to the indexer utilities.

    @source_dir is the source directory for the data that are used
    during the index construction.
    """
    def __init__(self, source_dir: str):
        self.__indexer = Indexer(source_dir)

    @timeit("Query executed in:")
    def __search(self, query: str):
        """ Searches for @query and prints results.
        """
        results = 0
        for i in self.__indexer.yield_search_result(query):
            print(i)
            results += 1
        print("{0:d} results.".format(results), end=' ')

    def start_prompt(self, prompt: str="query> "):
        """ Starts the prompt.
        """
        print()
        query = input(prompt)
        while not query == ":q":
            if query == '\n':
                continue
            elif query == ":index" or query == ":i":
                pprint.pprint(self.__indexer.index)
            elif query.startswith(":save_index"):
                try:
                    self.__indexer.save_index(query.split()[1])
                except IndexError:
                    print("error: need destination. Example:")
                    print("%s :save_index /home/joe/index.txt" % prompt)
            else:
                self.__search(query)
            query = input("\nquery> ")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("error: bad argument count")
        print("usage: %s /path/to/source/directory" % sys.argv[0])
        sys.exit(1)

    client = Client(sys.argv[1])
    client.start_prompt()

# vim: set ts=4 sts=4 sw=4 :

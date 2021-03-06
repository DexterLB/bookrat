import re
import json
from pyswip import Prolog
from tempfile import mkdtemp
import os
from os import path
import shutil
from itertools import islice
import time

from .cache import BulkCall

class Stemmer:
    def __init__(self, rules_file, stop_words=[], dictionary=[], cache=None):
        self.prolog = Prolog()
        self.read_prolog(rules_file)
        self.load_dictionary(dictionary)
        self.load_stop_words(stop_words)

        # it appears that prolog is fastest when processing about 1000
        # words at a time
        self.stem_iter = BulkCall(self.stem_multi, at_once=1000, cache=cache, stop_words=stop_words)

    def __call__(self, words):
        return self.stem_iter(words)

    def stem(self, word):
        return (
            decode(resp['X']) for resp in
            self.query('base_of(' + encode(word) + ', X)')
        )


    def stem_multi(self, words):
        try:
            encoded_words = ', '.join((encode(word) for word in words))
            result = next(self.query('bases_of([' + encoded_words + '], X)'))
            return [decode(atom.value) for atom in result['X']]
        except Exception as exc:
            raise Exception(
                'error while processing these words: ' +
                ', '.join(('`' + word + '`' for word in words)) +
                '\n' +
                str(exc)
            )


    def load_dictionary(self, dictionary):
        for word in dictionary:
            self.add_base_word(word.text, word.type)

    def load_stop_words(self, stop_words):
        self.stop_words = set(stop_words)

    def add_base_word(self, text, word_type):
        self.prolog.assertz(word_type + "(" + encode(text) + ")")

    def read_prolog(self, source_file):
        with open(source_file, 'r') as f:
            code = f.read()

        code = encode_prolog(code)

        self.execute_prolog(code)

    def execute_prolog(self, code):
        tempdir = mkdtemp()
        try:
            filename = path.join(tempdir, 'code.pl')

            with open(filename, 'w') as f:
                f.write(code)

            self.prolog.consult(filename)
        finally:
            shutil.rmtree(tempdir)

    def query(self, query):
        return self.prolog.query(query)

def encode(text):
    return ''.join(('t' + str(ord(x)) for x in text))

def decode(atom):
    return ''.join((chr(int(x)) for x in atom.split('t') if x))

def encode_prolog(code):
    return re.sub(r'"([^"]+)"', encode_match, code)

def encode_match(match):
    text, = match.groups()
    return encode(text)


class Word:
    def __init__(self, text, word_type):
        self.text = text
        self.type = word_type

def load_dictionary(filename):
    with open(filename) as f:
        for subdictionary in json.load(f):
            word_type = subdictionary['type']
            for word in subdictionary['words']:
                yield Word(word, word_type)

def load_stop_words(filename):
    stop_words = set()
    with open(filename) as f:
        for line in f:
            stop_words.add(line.strip())
    return stop_words

if __name__ == '__main__':
    s = Stemmer(
        os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            'bulgarian_grammar.pl'
        ),
        load_dictionary(
            os.path.join(
                os.path.dirname(os.path.realpath(__file__)),
                'bulgarian_words.json'
            )
        )
    )

    with open('/tmp/foo.txt') as f:
        words = json.load(f)

    start = time.time()
    result = list(s(words))
    end = time.time()

    us_perword = ((end - start) / len(words)) * 100000

    print(words[0] + ' -> ' + result[0])
    print(words[1] + ' -> ' + result[1])
    print('stemming', len(words), 'words took', end - start, 'sec')
    print('e.g.', us_perword, 'microseconds per word')

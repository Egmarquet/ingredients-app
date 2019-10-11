import sys
import os

from collections import Counter
from fractions import Fraction

import pycrfsuite

import nltk
from nltk.stem.porter import *
from nltk.tag import pos_tag
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

class Tagger:
    def __init__(self, model_path):
        self.lemmatizer = WordNetLemmatizer()
        self.stemmer = PorterStemmer()
        self.stop_words = set(stopwords.words('english'))

        self.tagger = pycrfsuite.Tagger()
        self.tagger.open(model_path)

    def tokenize(self, sentence):
        sentence = sentence.replace('-', ' - ')
        tokenized_sent = word_tokenize(sentence)

        if tokenized_sent:
            if tokenized_sent[0] in ['``','""',"''"]:
                tokenized_sent.pop(0)
            if tokenized_sent[-1] in ['``','""',"''"]:
                tokenized_sent.pop(-1)

        return tokenized_sent

    def is_plural(self, word):
        lemma = self.lemmatizer.lemmatize(word, 'n')
        plural = True if word is not lemma else False
        return plural

    def is_stop_word(self, word):
        return True if word in self.stop_words else False

    def is_fraction(self, word):
        try:
            frac = Fraction(word)
            dec = round(frac.numerator/frac.denominator, 2)
            if dec % 1 == 0:
                return False
            else:
                return True
        except ValueError:
            return False

    def sentence_to_features(self, tokens, pos_tags):
        sentence_features = []

        for i, word in enumerate(tokens):
            word_features = [
                'bias',
                f'word={word.lower()}',
                f'wordStemmed={self.stemmer.stem(word.lower())}',
                f'wordIsPlural={self.is_plural(word)}',
                f'wordIsNumeric={word.isnumeric()}',
                f'wordIsFraction={self.is_fraction(word)}',
                f'wordIsStopWord={self.is_stop_word(word)}',
                f"wordPOSTag={pos_tags[i]}",
                f"wordPOSTag2={pos_tags[i][:2]}",
                f'wordAtBeginning={True if i == 0 else False}',
                f"wordAtEnd={True if i == len(tokens)-1 else False}"
            ]

            if i > 0:
                word_m1 = tokens[i-1]
                word_features.extend([
                    f'-1:word={word_m1.lower()}',
                    f'-1:wordStemmed={self.stemmer.stem(word_m1.lower())}',
                    f"-1:wordPOSTag={pos_tags[i-1]}",
                    f"-1:wordPOSTag2={pos_tags[i-1][:2]}",
                    f'-1:wordIsPlural={self.is_plural(word_m1)}',
                    f'-1:wordIsNumeric={word_m1.isnumeric()}',
                    f'-1:wordIsFraction={self.is_fraction(word_m1)}',
                    f'-1:wordIsStopWord={self.is_stop_word(word_m1)}'
                ])

            if i < len(tokens)-1:
                word_p1 = tokens[i+1]
                word_features.extend([
                    f'+1:word={word_p1.lower()}',
                    f'+1:wordStemmed={self.stemmer.stem(word_p1.lower())}',
                    f"+1:wordPOSTag={pos_tags[i+1]}",
                    f"+1:wordPOSTag2={pos_tags[i+1][:2]}",
                    f'+1:wordIsPlural={self.is_plural(word_p1)}',
                    f'+1:wordIsNumeric={word_p1.isnumeric()}',
                    f'+1:wordIsFraction={self.is_fraction(word_p1)}',
                    f'+1:wordIsStopWord={self.is_stop_word(word_p1)}'

                ])
            sentence_features.append(word_features)
        return sentence_features

    def evaluate(self, sentence):
        tokenized_sentence = self.tokenize(sentence)
        pos_tags = [pos_tag([word])[0][1] for word in tokenized_sentence]
        features = self.sentence_to_features(tokenized_sentence, pos_tags)
        tags = self.tagger.tag(features)
        probs = [self.tagger.marginal(tags[i], i) for i in range(len(tags))]


        return [tokenized_sentence, tags, probs]

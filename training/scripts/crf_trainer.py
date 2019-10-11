import sys
import random
import json
from collections import Counter
from fractions import Fraction

import pycrfsuite

import nltk
from nltk.stem.porter import *
from nltk.tag import pos_tag
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

wnl = WordNetLemmatizer()
stemmer = PorterStemmer()
stop_words = set(stopwords.words('english'))

def isplural(word):
    lemma = wnl.lemmatize(word, 'n')
    plural = True if word is not lemma else False
    return plural

def isstopWord(word):
    return True if word in stop_words else False

def isfraction(word):
    try:
        frac = Fraction(word)
        dec = round(frac.numerator/frac.denominator, 2)
        if dec % 1 == 0:
            return False
        else:
            return True
    except ValueError:
        return False

def train_crf(path_in, path_out):
    data = []
    with open(path_in, "r+", encoding="utf8") as f:
        data = json.load(f)

    x_train = []
    y_train = []

    print("Parsing File")
    for i, sentence in enumerate(data):
        tokens = sentence['tokens']
        labels = list(map(lambda x: x if x else 'O', sentence['labels'])) #forgot to label
        pos = sentence['pos']
        features = sentence_to_features(tokens, pos)

        x_train.append(features)
        y_train.append(labels)

        if i%1000 == 0:
            print(i)

    print("Training Model")
    trainer = pycrfsuite.Trainer(verbose=False)
    trainer.set_params({
        'c1': 0.1,   # coefficient for L1 penalty
        'c2': 0.1,  # coefficient for L2 penalty
        'max_iterations': 100,  # stop earlier
        'feature.possible_transitions': True
    })

    for xseq, yseq in zip(x_train, y_train):
        trainer.append(xseq, yseq)

    trainer.train(f'{path_out}.crfmodel')

def tokenize(sentence):
    sentence = sentence.replace('-', ' - ')
    tokenized_sent = word_tokenize(sentence)

    if tokenized_sent:
        if tokenized_sent[0] in ['``','""',"''"]:
            tokenized_sent.pop(0)
        if tokenized_sent[-1] in ['``','""',"''"]:
            tokenized_sent.pop(-1)

    return tokenized_sent

def sentence_to_features(tokens, pos_tags):
    sentence_features = []

    for i, word in enumerate(tokens):
        word_features = [
            'bias',
            f'word={word.lower()}',
            f'wordStemmed={stemmer.stem(word.lower())}',
            f'wordIsPlural={isplural(word)}',
            f'wordIsNumeric={word.isnumeric()}',
            f'wordIsFraction={isfraction(word)}',
            f'wordIsStopWord={isstopWord(word)}',
            f"wordPOSTag={pos_tags[i]}",
            f"wordPOSTag2={pos_tags[i][:2]}",
            f'wordAtBeginning={True if i == 0 else False}',
            f"wordAtEnd={True if i == len(tokens)-1 else False}"
        ]

        if i > 0:
            word_m1 = tokens[i-1]
            word_features.extend([
                f'-1:word={word_m1.lower()}',
                f'-1:wordStemmed={stemmer.stem(word_m1.lower())}',
                f"-1:wordPOSTag={pos_tags[i-1]}",
                f"-1:wordPOSTag2={pos_tags[i-1][:2]}",
                f'-1:wordIsPlural={isplural(word_m1)}',
                f'-1:wordIsNumeric={word_m1.isnumeric()}',
                f'-1:wordIsFraction={isfraction(word_m1)}',
                f'-1:wordIsStopWord={isstopWord(word_m1)}'
            ])

        if i < len(tokens)-1:
            word_p1 = tokens[i+1]
            word_features.extend([
                f'+1:word={word_p1.lower()}',
                f'+1:wordStemmed={stemmer.stem(word_p1.lower())}',
                f"+1:wordPOSTag={pos_tags[i+1]}",
                f"+1:wordPOSTag2={pos_tags[i+1][:2]}",
                f'+1:wordIsPlural={isplural(word_p1)}',
                f'+1:wordIsNumeric={word_p1.isnumeric()}',
                f'+1:wordIsFraction={isfraction(word_p1)}',
                f'+1:wordIsStopWord={isstopWord(word_p1)}'

            ])
        sentence_features.append(word_features)
    return sentence_features

def evaluate_sentence(model, sentence):
    sentence = tokenize(sentence)
    pos_tags = [pos_tag([word])[0][1] for word in sentence]
    features = sentence_to_features(sentence, pos_tags)
    tags = model.tag(features)
    for i, sent in enumerate(sentence):
        print(sent, tags[i])

# model evaluation
def print_state_features(state_features):
    for (attr, label), weight in state_features:
        print("%0.6f %-6s %s" % (weight, label, attr))

def print_transitions(trans_features):
    for (label_from, label_to), weight in trans_features:
        print("%-6s -> %-7s %0.6f" % (label_from, label_to, weight))

if __name__ == '__main__':
    #train_crf(".\\training_set.json", "iter_2")
    tagger = pycrfsuite.Tagger()
    tagger.open(".\\iter_2.crfmodel")
    evaluate_sentence(tagger,"4 large round elephant tusks")
    info = tagger.info()

    s = """
    print("Top likely transitions:")
    print_transitions(Counter(info.transitions).most_common(15))

    print("\nTop unlikely transitions:")
    print_transitions(Counter(info.transitions).most_common()[-15:])

    print("Top positive:")
    print_state_features(Counter(info.state_features).most_common(100))

    print("\nTop negative:")
    print_state_features(Counter(info.state_features).most_common()[-20:])
    """

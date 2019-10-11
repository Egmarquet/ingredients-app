from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from crf_tagger import Tagger
import json

app = Flask(__name__)
CORS(app)
tagger = Tagger("iter_2.crfmodel")


@app.route("/api/tag", methods = ['POST'])
def tag():
    try:
        if request.method == "POST":
            data = json.loads(request.data)
            raw_sents = data['data']
            out = tag_sents(raw_sents)
            return jsonify(out)
        else:
            return 'error', 500

    except Exception as e:
        print(e)
        return 'error', 500


def tag_sents(raw_sents):
    response = {'data':[]}
    sentences = raw_sents.split("\n")
    for line, sent in enumerate(sentences):
        tokenized_sentence, labels, probs = tagger.evaluate(sent)
        if not labels:
            response['data'].append({'tokens':tokenized_sentence, 'line':line, 'valid': False})
            continue

        ingredients = combine_tags(tokenized_sentence, labels, "INGR_B", "INGR_I"," ")
        units = combine_tags(tokenized_sentence, labels, "UNIT_B", "UNIT_I"," ")
        amounts = combine_tags(tokenized_sentence, labels, "AMT_B", "AMT_I"," ")
        mult = combine_tags(tokenized_sentence, labels, "MULT", "")

        #No valid ingredients
        if not ingredients:
            response['data'].append({'tokens':tokenized_sentence, 'line':line, 'valid': False})

        else:
            response['data'].append({'tokens':tokenized_sentence, 'line':line, 'ingredients':ingredients, 'units':units, 'amounts':amounts, 'mult':mult, 'valid': True})

    return response

def tokenized_to_ranges(tokenized_sent):
    """
    Get the substring character ranges for each token
    1 cup milk:

    """
    ranges = []
    for i, token in enumerate(tokenized_sent):
        if i == 0:
            ranges.append([0,len(token)-1])
        else:
            ranges.append([ranges[i-1][1]+1,ranges[i-1][1]+len(token)])
    return ranges

def combine_tags(tokenized_sent, labels, tag_B, tag_I, join_delim=None):
    out = []
    current = []
    ranges = tokenized_to_ranges(tokenized_sent)
    #look for contiguous tag_b tag_I tag_I ...
    for i, tag in enumerate(labels):
        if tag == tag_B and not current:
            # new case
            current = []
            current.append(i)

        elif tag == tag_B and current:
            # pop new ingredient case
            out.append({'words':[tokenized_sent[i] for i in current], 'ranges':[i for i in current]})
            current = []
            current.append(i)

        elif tag == tag_I and current:
            current.append(i)

        else:
            if current:
                out.append({'words':[tokenized_sent[i] for i in current], 'ranges':[i for i in current]})
                current = []

    #end of sentence
    if current:
        out.append({'words':[tokenized_sent[i] for i in current], 'ranges':[i for i in current]})

    print(out)
    if join_delim:
        for entry in out:
            entry['words'] = join_delim.join(entry['words'])


    return out

if __name__ == '__main__':
    app.run()

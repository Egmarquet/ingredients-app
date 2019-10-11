import re
from fractions import Fraction
import decimal
import json
from nltk.stem.porter import *
from nltk.tag import pos_tag
from nltk.tokenize import word_tokenize
import random
import sys
import os
from copy import deepcopy
banned_punct = ['"','~',',',"(",")","."]
stemmer = PorterStemmer()

# Takes a while at runtime so will have ot run overnight eventually
java_path = "C:\\Program Files\\Java\\jdk-12.0.2\\bin\\java.exe"
os.environ['JAVAHOME'] = java_path
path_stanford_pos_model = ".\\data\\stanford-postagger-2018-10-16\\models\\english-left3words-distsim.tagger"
path_to_jar = ".\\data\\stanford-postagger-2018-10-16\\stanford-postagger-3.9.2.jar"
st = StanfordPOSTagger(path_stanford_pos_model,path_to_jar)

numerical_unit_list = [
      "teaspoon", "tsp", "tea spoon", "tea spoons", "teaspoons", "ts",
      "tablespoon","tbsp", "tbs", "table spoon", "tbls", "tablespoons", "table spoons"
      "fluid ounce","fl oz","fluidounce", "fluidounces","floz", "fluid ounces", "fluid oz", "fl-oz", "fluid-ounce",
      "cup","c","cups",
      "pint","pt","pints","pts",
      "quart","qt","quarts", "qts",
      "gallon","gal","gallons","gals"
      "milliliter","ml","milliliters",
      "liter","L","liters",
      "milligram","mg","milligrams"
      "gram","g","grams",
      "kilogram","kg","kilograms",
      "pound","lb","lbs","pounds",
      "ounce","oz","ounces",
]

def reformat():
    """
    csv format:
        id,sentence,ingredient,amount,0,unit,comment

    Initial file Reformatting due to commas within data csv being treated as
    both plain text (when in quotations) and the actual delimiter

    """
    n = open("..\\nyt_dataset\\nyt_ingredients_reformatted.csv", "w+", encoding="utf8")
    with open("..\\nyt-ingredients-snapshot-2015.csv", encoding="utf8") as f:
        for line in f:
            # Reformatting nyt file for easier formatting
            in_quotes = False
            reformatted = ''
            for c in line:
                if c == '"':
                    if in_quotes == True:
                        in_quotes = False
                    else:
                        in_quotes = True
                if c == ',' and in_quotes:
                    c = '~'
                reformatted += c

            n.write(reformatted)
    n.close()

def tilde_to_comma(sentence):
    sentence = sentence.replace("~",",")
    return sentence

def tag_file():
    """
    Tags:

    UNIT_B: unit beginning
    UNIT_I: unit intermediate
    MULT: Multiplier amount for whole ingredients/n-oz-cans
    AMT_B: amount beginning
    AMT_I: amount intermediate
    INGR_B: ingredient beginning
    INGR_I: ingredient intermediate
    O: ommitted
    
    """
    json_out = []
    numerical_units = [tokenize(unit) for unit in numerical_unit_list]

    with open("..\\nyt_dataset\\nyt_ingredients_reformatted.csv", encoding="utf8") as f:
        for n, line in enumerate(f):
            try:
                id,sentence,ingr,amt_1,amt_2,unit,comment = line.split(",")
                tokenized_sentence = tokenize(sentence.replace("~",","))
                if not tokenized_sentence:
                    continue

                ingr = tokenize(ingr.replace("~",","))
                unit = tokenize(unit.replace("~",","))
                amt_1 = float(amt_1)
                amt_2 = float(amt_2)

                tagged_ingr = tag_ingredients(tokenized_sentence, ingr)
                tagged_units = tag_units(tokenized_sentence, numerical_units)
                tagged_amounts = tag_amounts(tokenized_sentence, amt_1, amt_2)

                # document this
                if "MULT" in tagged_amounts:
                    #print(tokenized_sentence)
                    pass

                if not any(tagged_ingr):
                    continue
                if not any(tagged_units) and unit:
                    continue
                if not any(tagged_amounts) and amt_1:
                    continue

                labels = combine_tag_arrays(tokenized_sentence,[tagged_ingr,tagged_units,tagged_amounts])
                pos = [t[1] for t in pos_tag(tokenized_sentence)]

                json_out.append({'tokens':tokenized_sentence,'labels':labels,'pos':pos})

                if n%1000 == 0:
                    print(n)
            except KeyboardInterrupt as e:
                sys.exit(1)

            except Exception as e:
                continue

    with open("..\\training_set.json", "w+", encoding="utf8") as f:
        js = json.dumps(json_out)
        f.write(js)

def write_tokenized():
    sf = open("..\\sf.txt", "w+", encoding="utf8")
    with open("..\\nyt_dataset\\nyt_ingredients_reformatted.csv", encoding="utf8") as f:
        for n, line in enumerate(f):
            id,sentence,ingr,amt_1,amt_2,unit,comment = line.split(",")
            tokenized_sentence = tokenize(sentence.replace("~",",")) #replacing inserted ~
            sf.write(f'{" ".join(tokenized_sentence)}\n')
    sf.close()

def tokenize(sentence):
    sentence = sentence.replace('-', ' - ')
    tokenized_sent = word_tokenize(sentence)

    if tokenized_sent:
        if tokenized_sent[0] in ['``','""',"''"]:
            tokenized_sent.pop(0)
        if tokenized_sent[-1] in ['``','""',"''"]:
            tokenized_sent.pop(-1)

    return tokenized_sent

def find_substring(list_1, list_2, stemming=False, lowercase=True):
    """
    Returns a list of indeicies of matching sublists of list_2 in list_1
    """
    substrings = []
    if not list_1 or not list_2:
        return []

    if lowercase:
        list_1 = [word.lower() for word in list_1]
        list_2 = [word.lower() for word in list_2]

    if stemming:
        main_string_list = [stemmer.stem(word) for word in list_1]
        substring_list = [stemmer.stem(word) for word in list_2]

    #sliding window
    for i in range(len(list_1)-len(list_2)+1):
        window = [list_1[i+j] for j in range(len(list_2))]
        if window == list_2:
            substrings.append([i, i+len(list_2)-1])

    return substrings

def tag_ingredients(tokenized_sentence, tokenized_ingredients):
    """
    Tagging should be safe, only looking for substrings = to ingredient substrings
    If no ingredient substring is found in the split_sentences
    """
    tag_arr = [None for i in range(len(tokenized_sentence))]

    if not tokenized_ingredients:
        return tag_arr

    substring_index = find_substring(tokenized_sentence, tokenized_ingredients, lowercase=True)
    if substring_index:
        for start, fin in substring_index:
            for i in range(start,fin+1):
                if i == start:
                    tag_arr[i] = 'INGR_B'
                else:
                    tag_arr[i] = 'INGR_I'
    else:
        return tag_arr

    return tag_arr

def tag_units(tokenized_sentence, unit_words):
    """
    Unit tagging should be done just by a simple match on the stemmed unit string
    """
    tag_arr = [None for i in range(len(tokenized_sentence))]
    unit_tags_ind = []
    for unit in unit_words:
        substring_index = find_substring(tokenized_sentence,unit, lowercase=True)
        if substring_index:
            unit_tags_ind.append(substring_index)

    for uti in unit_tags_ind:
        for substring_index in unit_tags_ind:
            for start, fin in substring_index:
                for i in range(start,fin+1):
                    if i == start:
                        tag_arr[i] = 'UNIT_B'
                    else:
                        tag_arr[i] = 'UNIT_I'

    return tag_arr

def tag_amounts(tokenized_sentence, amt_1, amt_2):
    all_amounts = [] # [[number in decimal form, index], ... ]
    tag_arr = [None for i in range(len(tokenized_sentence))]
    # extracting numbers
    for i, word in enumerate(tokenized_sentence):
        try:
            amt_word = Fraction(word)
            amt_dec = round(amt_word.numerator/amt_word.denominator, 2)
            if amt_dec % 1 == 0:
                all_amounts.append([amt_dec, [i]])
            # if the current number is a fraction and the previous amount is a whole number,
            # combine fractions to the nearest preceeding whole number
            elif all_amounts and \
            all_amounts[-1][0].is_integer() and \
            all_amounts[-1][0] + 2 >= i: #within 2 indicies case
                all_amounts[-1][0] += amt_dec
                all_amounts[-1][1].append(i)
            else:
                all_amounts.append([amt_dec, [i]])
        except ValueError:
            continue

    for amount, inds in all_amounts:
        #checking if, AMT_1 == amount or AMT_2 == amt with rounding errors
        if (amt_1 >= amount - 0.1 and amt_1 <= amount + 0.1) \
        or (amt_2 >= amount - 0.1 and amt_2 <= amount + 0.1):
            for i in inds:
                if i == inds[0]:
                    tag_arr[i] = "AMT_B"
                else:
                    tag_arr[i] = "AMT_I"

    # cans/bottles/bags/etc case:
    # do not worry about 2 amounts
    # The multiplier must be a whole number
    mult = []
    if not any(tag_arr):
        # try to modifiy the all_amounts array by combining whole numbers with the next amount
        for i, (amt, inds) in enumerate(all_amounts):
            if i>=1 and all_amounts[i-1][0]%1 == 0:
                m_amt = all_amounts[i-1][0]*amt
                m_inds = deepcopy(all_amounts[i-1][1])
                m_inds.extend(inds)
                mult.append([m_amt, m_inds])
        # If not an empty case:
        if mult:
            for m_amt, m_inds in mult:
                if (amt_1 >= m_amt - 0.1 and amt_1 <= m_amt + 0.1):
                    for i in m_inds:
                        if i == m_inds[0]:
                            tag_arr[i] = "MULT"
                        elif i == m_inds[1]:
                            tag_arr[i] = "AMT_B"
                        else:
                            tag_arr[i] = "AMT_I"

    return tag_arr

def combine_tag_arrays(tokenized_sentence, arrays):
    """
    merge into a single array, ignoring None entries
    """
    tag_arr = [None for i in range(len(tokenized_sentence))]
    for array in arrays:
        for i, tag in enumerate(array):
            if tag:
                tag_arr[i] = tag

    return tag_arr


if __name__ == '__main__':
    tag_file()

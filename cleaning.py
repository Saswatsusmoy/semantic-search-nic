import difflib
import string, re
from functools import lru_cache
from spellchecker import SpellChecker
import time

spell = SpellChecker()

lis = []
with open("Data Processing/lemmatized_words.txt", 'r') as file:
    text = file.read()
    word_list = text.split()
    lis.extend(word_list)

def is_valid(word):
    return word in spell

def correct_words(text, word_list = lis, cutoff=0.7):
    words = text.split()
    corrected_text = []
    word_list_tuple = tuple(word_list)
    @lru_cache(maxsize=2048)
    def get_best_match(word):
        close_matches = difflib.get_close_matches(word, word_list_tuple, n=1, cutoff=cutoff)
        return close_matches[0] if close_matches else word
    for word in words:
        if is_valid(word):
            corrected_text.append(word)
        else:
            corrected_text.append(get_best_match(word))
    print(" ".join(corrected_text))
    return " ".join(corrected_text)



# test_list = [
#     "Manufactue", "potein", "flopou", "fying", "othe", "ceeals", "pint", "electonic", 
#     "foyom", "intenet", "Goeing", "cheies", "sou", "Hiqghe", "degee", "Manufjtue", 
#     "holdes", "Geneal", "Tecnical", "maciney", "te", "gain", "mllling", "industy", 
#     "troug", "mdains", "andling", "iglr", "andicapped", "Reproxproduction", "Repakr", 
#     "periperak", "periperak", "Retaik", "sake", "fertikisers", "pezs", "macinery", 
#     "tooks", "oter", "ctivities", "professionk", "membersip", "orgniztions", "ckss", 
#     "inckudes", "ctivities", "ssocitions", "writers", "pinters", "kwyers", "journkists", 
#     "simikr", "orgnistions", "Mnufcture", "prepred", "cokouring", "mtter", "pints", 
#     "Mnufcture", "rtickes", "instkktion", "industrik", "mchinery", "equijent", "biskit"
# ]

# test_out = [
#     "Manufacture", "protein", "flour", "frying", "other", "cereals", "print", "electronic", 
#     "form", "internet", "Going", "cherries", "sour", "Higher", "degree", "Manufacture", 
#     "holders", "General", "Technical", "machinery", "the", "grain", "milling", "industry", 
#     "through", "mains", "handling", "higher", "handicapped", "Reproduction", "Repair", 
#     "peripheral", "peripheral", "Retail", "sale", "fertilizers", "peas", "machinery", 
#     "tools", "other", "activities", "professional", "membership", "organizations", "class", 
#     "includes", "activities", "associations", "writers", "painters", "lawyers", "journalists", 
#     "similar", "organizations", "Manufacture", "prepared", "colouring", "matter", "paints", 
#     "Manufacture", "articles", "installation", "industrial", "machinery","equipment", "biscuit"
# ]
# cou_r = 0
# cou_w = 0
# cou_un = 0
# tot = 0 

# def clean_sentence(input_string):
#     input_string = input_string.replace("-", " ").replace("–", " ").replace("—", " ").replace(':', ' ').replace("।", "")
#     if not isinstance(input_string, str):
#         return ""    
#     remove_chars = string.punctuation + '|'
#     for char in remove_chars:
#         input_string = input_string.replace(char, "")
#     result = input_string.strip().lower()
#     result = re.sub(r'\s+', ' ', result)
#     return result

# start = time.time()
# for i in range(len(test_list)):
#     wrong = test_list[i]
#     corrected = correct_words(clean_sentence(wrong), word_list)
#     if clean_sentence(corrected) == clean_sentence(test_out[i]):
#         cou_r = cou_r + 1
#     elif clean_sentence(corrected[:-1]) == clean_sentence(test_out[i]) or clean_sentence(corrected) == clean_sentence(test_out[i][:-1]):
#         cou_r = cou_r + 1
#     elif clean_sentence(corrected) == clean_sentence(wrong):
#         cou_un = cou_un + 1        
#     else:
#         cou_w = cou_w + 1
#         print("Wrong: ", wrong, "Corrected: ", corrected, "Expected: ", test_out[i])
#     tot = tot+1
# end = time.time()

# print(f"Correct: {cou_r} Wrong: {cou_w} Untouched: {cou_un} Total: {tot}")
# print("Accuracy:", cou_r/(tot-cou_un)*100)
# print(f"Time taken: {end-start}")

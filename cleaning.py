from spellchecker import SpellChecker
import time, re, string

def clean_sentence(input_string):
    input_string = input_string.replace("-", " ").replace("–", " ").replace("—", " ").replace(':', ' ').replace("।", "")
    if not isinstance(input_string, str):
        return ""    
    remove_chars = string.punctuation + '|'
    for char in remove_chars:
        input_string = input_string.replace(char, "")

    result = input_string.strip().lower()
    result = re.sub(r'\s+', ' ', result)
    spell = SpellChecker()
    words = result.split()
    unique_words = set(words)
    
    corrections = {word: spell.correction(word) for word in unique_words}
    corrected_text = ' '.join([corrections[word] for word in words])
    return corrected_text


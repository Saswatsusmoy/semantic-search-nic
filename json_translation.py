import pandas as pd
from azure.ai.translation.text import TextTranslationClient
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError

azure_ai_translator_key = ""
azure_ai_translator_region = ""

credential = AzureKeyCredential(azure_ai_translator_key)

text_translator = TextTranslationClient(
    credential=credential,
    region=azure_ai_translator_region
)

response = text_translator.get_supported_languages()

def print_languages(label, languages):
    """
    Print supported languages of Azure AI Translator
    """
    print("\033[1;31;34m")
    
    if languages is not None:
        print(f"Number of supported {label} languages = {len(languages)}\n")
        print(f"{label.capitalize()} languages:")

        for idx, (key, value) in enumerate(languages.items(), start=1):
            print(f"{idx:03}\t{key:10} {value.name} ({value.native_name})")

    else:
        print(f"No supported {label} languages.")
        
print_languages("translation", response.translation)

lang_list = []

if response.translation is not None:
    for key, value in response.translation.items():
        lang_list.append(
            {
                "Language_Code": key,
                "Language_Name": value.name,
                "Native_Name": value.native_name,
            }
        )

df_languages = pd.DataFrame(lang_list)
language_dict = df_languages.set_index("Language_Code")["Language_Name"].to_dict()
language_full_names = list(language_dict.values())
language_full_names.sort()
language_codes = list(language_dict.keys())
language_codes.sort()
reverse_language_names = {v: k for k, v in language_dict.items()}

def get_language_code(language_name):
    return reverse_language_names.get(language_name)

print(get_language_code("English"))  # Should print the language code for English


def azure_ai_translator(mytext, source_lang, target_lang):
    try:
        credential = AzureKeyCredential(azure_ai_translator_key)
        
        text_translator = TextTranslationClient(
            credential=credential, region=azure_ai_translator_region)
        input_text_elements = [mytext]
        source_lang_code = get_language_code(source_lang)
        target_lang_code = get_language_code(target_lang)
        
        if not source_lang_code or not target_lang_code:
            raise ValueError(f"Invalid source or target language code. Source: {source_lang_code}, Target: {target_lang_code}")


        response = text_translator.translate(body=input_text_elements,
                                             from_language=source_lang_code, to_language=[target_lang_code])
        translation = response[0] if response else None

        if translation:
            detected_language = translation.detected_language
            if detected_language:
                print(f"Detected languages of the input text: {detected_language.language} with score = {detected_language.score}.")
            for translated_text in translation.translations:
                print(f"\nText to translate to: '{translated_text.to}'")
            return translated_text.text

    except HttpResponseError as exception:
        if exception.error is not None:
            print(f"Error Code: {exception.error.code}")
            print(f"Message: {exception.error.message}")
    except ValueError as e:
        print(e)


###############

import json
from tqdm import tqdm

def translate_text(text):    
    if pd.isna(text):
        return None
    return azure_ai_translator(text, "English", "Tamil")

def azure_ai_translator(mytext, source_lang, target_lang):
    try:
        credential = AzureKeyCredential(azure_ai_translator_key)
        text_translator = TextTranslationClient(
            credential=credential, region=azure_ai_translator_region)
        input_text_elements = [mytext]

        source_lang_code = get_language_code(source_lang)
        target_lang_code = get_language_code(target_lang)
        
        if not source_lang_code or not target_lang_code:
            raise ValueError(f"Invalid source or target language code. Source: {source_lang_code}, Target: {target_lang_code}")

        response = text_translator.translate(body=input_text_elements,
                                             from_language=source_lang_code, to_language=[target_lang_code])
        translation = response[0] if response else None

        if translation:
            detected_language = translation.detected_language
            if detected_language:
                print(f"Detected languages of the input text: {detected_language.language} with score = {detected_language.score}.")
            for translated_text in translation.translations:
                print(f"\nText to translate to: '{translated_text.to}'")
                return translated_text.text   
        return None  
    except HttpResponseError as exception:
        if exception.error is not None:
            print(f"Error Code: {exception.error.code}")
            print(f"Message: {exception.error.message}")
    except ValueError as e:
        print(e)

def process_file():
    with open('output.json', encoding='utf-8') as f:
        data = json.load(f)

    for entry in tqdm(data, desc="Processing entries", unit="entry"):
        if 'Vector-Embedding_SubClass' in entry:
            del entry['Vector-Embedding_SubClass']
        
        if 'Description' in entry:
            entry['Description_tamil'] = translate_text(entry['Description'])
            print(f"Translated Description: {entry['Description_tamil']}")
            if 'Inclusion from Exclusion' in entry:
                entry['Inclusion from Exclusion_tamil'] = translate_text(entry['Inclusion from Exclusion'])
            else:
                entry['Inclusion from Exclusion_tamil'] = None
        else:
            print(f"Error: 'Description' not found in entry {entry}")
            entry['Description_tamil'] = None
            entry['Inclusion from Exclusion_tamil'] = None

    with open('output_tamil.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        
    print("Translation completed and saved to 'output_tamil.json'")

process_file()

with open('output_tamil.json', encoding='utf-8') as f:
    data = json.load(f)

for entry in data:
    entry.pop('Description', None)
    entry.pop('Inclusion from Exclusion', None)
    
    if 'Description_tamil' in entry:
        entry['Description'] = entry.pop('Description_tamil')

    if 'Inclusion from Exclusion_tamil' in entry:
        entry['Inclusion from Exclusion'] = entry.pop('Inclusion from Exclusion_tamil')

    for key, value in entry.items():
        if value is None:
            entry[key] = pd.NA

with open('output_tamil.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=4, ensure_ascii=False)

print("File processed and saved as 'output_modified.json'.")


import json
import pandas as pd
import asyncio
from googletrans import Translator
from tqdm import tqdm

translator = Translator()


#ctrl+f _{lang_code} like "ta" to whatever you need
async def translate_text(text, lang_code='hi'):
    if pd.isna(text):
        return None
    translated = await translator.translate(text, src='en', dest=lang_code)
    return translated.text


async def process_file():
    with open('output.json', encoding='utf-8') as f:
        data = json.load(f)

    for entry in tqdm(data, desc="Processing entries", unit="entry"):
        if 'Vector-Embedding_SubClass' in entry:
            del entry['Vector-Embedding_SubClass']
        
        if 'Description' in entry:
            entry['Description_ta'] = await translate_text(entry['Description'], lang_code='ta')

            if 'Inclusion from Exclusion' in entry:
                entry['Inclusion from Exclusion_ta'] = await translate_text(entry['Inclusion from Exclusion'], lang_code='ta')
            else:
                entry['Inclusion from Exclusion_ta'] = None
        else:
            print(f"Error: 'Description' not found in entry {entry}")

            entry['Description_ta'] = None
            entry['Inclusion from Exclusion_ta'] = None

    with open('output_ta.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print("Translation completed and saved to 'translated_output.json'")

asyncio.run(process_file())

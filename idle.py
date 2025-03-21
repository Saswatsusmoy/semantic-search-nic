import json

with open('output_tamil.json', encoding='utf-8') as f:
    data = json.load(f)

for entry in data:
    # Remove 'Description' and 'Inclusion from Exclusion'
    entry.pop('Description', None)
    entry.pop('Inclusion from Exclusion', None)
    
    # Rename 'Description_tamil' to 'Description'
    if 'Description_tamil' in entry:
        entry['Description'] = entry.pop('Description_tamil')
    
    # Rename 'Inclusion from Exclusion_tamil' to 'Inclusion from Exclusion'
    if 'Inclusion from Exclusion_tamil' in entry:
        entry['Inclusion from Exclusion'] = entry.pop('Inclusion from Exclusion_tamil')

    # Replace 'null' values with None
    for key, value in entry.items():
        if value is None:
            entry[key] = None

# Save the modified data back to the file
with open('output_tamil.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=4, ensure_ascii=False)

print("File processed and saved as 'output_tamil.json'.")

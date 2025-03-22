import json
import os
import torch
from transformers import AutoTokenizer, AutoModel
from tqdm import tqdm
import numpy as np
import pandas as pd

# Define paths to input and output files
hindi_file_path = "c:/Users/Hp/Desktop/COLLEGE/SEM 6/IIT_GND_HACK_THE_FUTURE/semantic-search-nic/output_hindi.json"
tamil_file_path = "c:/Users/Hp/Desktop/COLLEGE/SEM 6/IIT_GND_HACK_THE_FUTURE/semantic-search-nic/output_tamil.json"

# Function to load JSON data
def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

# Load model and tokenizer
print("Loading Vyakyarth model and tokenizer...")
model_name = "krutrim-ai-labs/Vyakyarth"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)

# Check for GPU availability
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Using device: {device}")
model.to(device)

# Function to generate embeddings for full sentences
def generate_embedding(text):
    if not text or pd.isna(text):
        # Return a zero vector if text is empty
        return [0.0] * 768  # Assuming the embedding dimension is 768
    
    # Process the entire text as one unit to get sentence-level embeddings
    # Tokenize the full text, ensuring we don't split it into separate sentences
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
    inputs = {key: val.to(device) for key, val in inputs.items()}
    
    with torch.no_grad():
        outputs = model(**inputs)
    
    # Get sentence-level embeddings by mean pooling across all tokens
    # This produces a single vector representing the entire text
    attention_mask = inputs['attention_mask']
    token_embeddings = outputs.last_hidden_state
    
    # Apply attention mask to get meaningful token embeddings only
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
    sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
    sentence_embeddings = sum_embeddings / sum_mask
    
    # Convert to list for JSON serialization
    return sentence_embeddings.squeeze().cpu().numpy().tolist()

# Process each JSON file
def process_file(file_path):
    print(f"Processing {file_path}...")
    data = load_json(file_path)
    
    # Check if the data is a list or a dictionary
    if isinstance(data, dict):
        # If it's a dictionary, convert to list of records
        records = list(data.values())
    else:
        records = data
    
    # Generate embeddings for each record
    for record in tqdm(records):
        if "Description" in record and record["Description"]:
            record["embeddings"] = generate_embedding(record["Description"])
    
    return records

# Process both files
try:
    # Process Hindi file
    hindi_data = process_file(hindi_file_path)
    with open(hindi_file_path, 'w', encoding='utf-8') as f:
        json.dump(hindi_data, f, ensure_ascii=False, indent=4)
    print(f"Updated {hindi_file_path} with embeddings")
    
    # Process Tamil file
    tamil_data = process_file(tamil_file_path)
    with open(tamil_file_path, 'w', encoding='utf-8') as f:
        json.dump(tamil_data, f, ensure_ascii=False, indent=4)
    print(f"Updated {tamil_file_path} with embeddings")
    
    print("Processing complete!")
except Exception as e:
    print(f"An error occurred: {str(e)}")

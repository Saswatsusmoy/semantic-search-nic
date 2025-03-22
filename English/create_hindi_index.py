import json
import faiss
import numpy as np
from tqdm import tqdm
from transformers import AutoTokenizer, AutoModel
import torch

# Hindi embedding model
hindi_model_name = "krutrim-ai-labs/Vyakyarth"

def get_hindi_embeddings(texts, batch_size=8):
    # Initialize the model
    tokenizer = AutoTokenizer.from_pretrained(hindi_model_name)
    model = AutoModel.from_pretrained(hindi_model_name)
    model.eval()
    
    embeddings = []
    print(f"Generating embeddings for {len(texts)} texts...")
    
    # Process texts in batches
    for i in tqdm(range(0, len(texts), batch_size)):
        batch_texts = texts[i:i+batch_size]
        with torch.no_grad():
            inputs = tokenizer(batch_texts, return_tensors="pt", padding=True, truncation=True, max_length=512)
            outputs = model(**inputs)
            # Use mean pooling of the last hidden state as the embedding
            batch_embeddings = outputs.last_hidden_state.mean(dim=1).squeeze().numpy()
            if len(batch_texts) == 1:
                batch_embeddings = np.array([batch_embeddings])
            embeddings.append(batch_embeddings)
    
    # Concatenate all batch embeddings
    all_embeddings = np.vstack(embeddings)
    return all_embeddings

def build_hindi_index():
    print("Loading Hindi data from output_hindi.json...")
    
    try:
        # Load Hindi data
        with open('output_hindi.json', 'r', encoding='utf-8') as f:
            hindi_data = json.load(f)
        
        print(f"Loaded {len(hindi_data)} Hindi entries")
        
        # Extract texts for embeddings
        texts = []
        for item in hindi_data:
            description = item.get('Description', '')
            if description:
                texts.append(description)
        
        # Generate embeddings
        print("Generating Hindi embeddings...")
        embeddings = get_hindi_embeddings(texts)
        
        # Create FAISS index
        print("Building FAISS index...")
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatL2(dimension)
        index.add(embeddings)
        
        # Save the index
        print("Saving Hindi FAISS index...")
        faiss.write_index(index, "hindi_faiss.index")
        
        print("Hindi index created successfully!")
        return True
    except Exception as e:
        print(f"Error building Hindi index: {e}")
        return False

if __name__ == "__main__":
    build_hindi_index()

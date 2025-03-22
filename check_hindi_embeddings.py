"""
Utility script to check the Hindi embeddings in output_hindi.json
"""

import json
import os
import sys
import numpy as np

def check_hindi_embeddings(file_path):
    """
    Check Hindi embeddings in the specified JSON file
    """
    try:
        if not os.path.exists(file_path):
            print(f"Error: File not found at {file_path}")
            return False
        
        print(f"Loading embeddings from {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"Loaded {len(data)} documents")
        
        # Count documents with embeddings
        with_embeddings = 0
        without_embeddings = 0
        embedding_dimensions = set()
        
        for doc in data:
            if "embeddings" in doc and doc["embeddings"]:
                with_embeddings += 1
                embedding_dimensions.add(len(doc["embeddings"]))
            else:
                without_embeddings += 1
        
        print(f"Documents with embeddings: {with_embeddings}")
        print(f"Documents without embeddings: {without_embeddings}")
        
        if embedding_dimensions:
            print(f"Embedding dimensions found: {embedding_dimensions}")
            
            # Check if embeddings are usable for FAISS
            sample_docs = [doc for doc in data if "embeddings" in doc and doc["embeddings"]]
            if sample_docs:
                sample_embeddings = [doc["embeddings"] for doc in sample_docs[:10]]  # Take first 10
                sample_array = np.array(sample_embeddings, dtype=np.float32)
                print(f"Sample embeddings array shape: {sample_array.shape}")
                print("Embeddings appear to be valid for FAISS indexing")
                return True
        else:
            print("No embeddings found in the file")
        
        return with_embeddings > 0
        
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {file_path}")
        return False
    except Exception as e:
        print(f"Error checking embeddings: {str(e)}")
        return False

if __name__ == "__main__":
    file_path = "output_hindi.json"
    
    # Use command line arg if provided
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    
    success = check_hindi_embeddings(file_path)
    sys.exit(0 if success else 1)

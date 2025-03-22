"""
Test script for the hybrid search implementation using FAISS with cosine similarity
"""

import os
import numpy as np
from faiss_index_manager import FAISSIndexManager
from sentence_transformers import SentenceTransformer
import time
import argparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_hybrid_search(query, top_k=5):
    """
    Test the hybrid search by running a query through the FAISS index
    
    Args:
        query (str): The search query
        top_k (int): Number of results to return
    """
    print(f"Testing hybrid search with query: '{query}'")
    
    # Load the sentence transformer model
    print("Loading sentence transformer model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Get connection string from environment
    connection_string = os.environ.get("MONGO_URI")
    if not connection_string:
        print("Error: MONGO_URI not found in environment variables")
        print("Please set this in your .env file")
        return
    
    # Initialize FAISS index manager
    faiss_manager = FAISSIndexManager(connection_string)
    
    # Load the index
    print("Loading FAISS index...")
    if not faiss_manager.load_index():
        print("Could not load index. Please make sure it's been created.")
        return
    
    # Generate embedding for the query
    print("Generating query embedding...")
    query_embedding = model.encode(query)
    
    # Perform search
    print(f"Searching for top {top_k} results...")
    start_time = time.time()
    
    search_results = faiss_manager.search(query_embedding, top_k=top_k)
    
    search_time = time.time() - start_time
    
    # Print results
    print(f"\nSearch completed in {search_time:.4f} seconds")
    print(f"Found {len(search_results)} results\n")
    
    if search_results:
        print("Result IDs and similarity scores:")
        for i, (doc_id, similarity) in enumerate(search_results):
            similarity_percent = round(similarity * 100, 2)
            print(f"{i+1}. Document ID: {doc_id}, Similarity: {similarity_percent}%")
    else:
        print("No results found.")
    
    print("\nNote: To see the actual document contents, you need to fetch them from MongoDB using the document IDs.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test the hybrid search implementation")
    parser.add_argument("query", nargs="?", default="software development", help="The query to search for")
    parser.add_argument("--top-k", type=int, default=5, help="Number of results to return")
    
    args = parser.parse_args()
    
    test_hybrid_search(args.query, args.top_k)

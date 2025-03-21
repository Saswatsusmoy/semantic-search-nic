"""
Test script for semantic search using local JSON data
"""

import os
import sys
import json
import time
import logging
import argparse
from sentence_transformers import SentenceTransformer
from faiss_index_manager import FAISSIndexManager
from vector_embeddings_manager import cached_get_embedding

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_local_search(query, top_k=5, mode="standard"):
    """
    Test semantic search with local JSON data
    
    Args:
        query: Search query text
        top_k: Number of results to return
        mode: Search mode (standard, strict, relaxed)
    """
    # Initialize FAISS manager
    faiss_manager = FAISSIndexManager()
    
    # Ensure JSON data exists
    json_path = os.path.join(os.path.dirname(__file__), "output.json")
    if not os.path.exists(json_path):
        logger.error(f"JSON file not found: {json_path}")
        logger.error("Please run convert_mongo_to_json.py first or ensure output.json exists")
        return False
    
    # Load the index or build it if necessary
    if not faiss_manager.load_index():
        logger.warning("Index not found, building it now...")
        success = faiss_manager.build_index()
        if not success:
            logger.error("Failed to build index")
            return False
    
    # Get embedding for the query
    logger.info(f"Getting embedding for query: '{query}'")
    query_embedding = cached_get_embedding(query, 'all-MiniLM-L6-v2')
    
    # Set thresholds based on mode
    thresholds = {
        "standard": 0.5,
        "strict": 0.7,
        "relaxed": 0.3
    }
    threshold = thresholds.get(mode, 0.5)
    
    # Perform search
    logger.info(f"Searching with mode '{mode}' (threshold: {threshold})")
    start_time = time.time()
    raw_results = faiss_manager.search(query_embedding, top_k=top_k * 2)
    search_time = time.time() - start_time
    
    # Filter by threshold
    filtered_results = [(doc_id, sim) for doc_id, sim in raw_results if sim >= threshold]
    
    # Load JSON data to get full documents
    with open(json_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    # Create a map for quick lookups
    doc_map = {str(doc["_id"]): doc for doc in json_data}
    
    # Format results
    formatted_results = []
    for doc_id, similarity in filtered_results[:top_k]:
        if doc_id in doc_map:
            doc = doc_map[doc_id]
            formatted_results.append({
                "id": doc_id,
                "title": doc.get("Sub-Class_Description", doc.get("Class_Description", "No Title")),
                "section": doc.get("Section", ""),
                "division": doc.get("Division", ""),
                "group": doc.get("Group", ""),
                "class": doc.get("Class", ""),
                "subclass": doc.get("Sub-Class", ""),
                "similarity": similarity,
                "similarity_percent": round(similarity * 100, 2)
            })
    
    # Print results
    print(f"\nSearch completed in {search_time:.3f} seconds")
    print(f"Query: '{query}'")
    print(f"Mode: {mode}")
    print(f"Found {len(formatted_results)} results\n")
    
    for i, result in enumerate(formatted_results):
        print(f"{i+1}. {result['title']} ({result['similarity_percent']}%)")
        print(f"   Section: {result['section']}, Division: {result['division']}, " 
              f"Group: {result['group']}, Class: {result['class']}, Sub-Class: {result['subclass']}")
        print()
    
    return True

def main():
    parser = argparse.ArgumentParser(description='Test semantic search with local JSON data')
    parser.add_argument('query', nargs='?', default='software development', help='Search query')
    parser.add_argument('--top-k', type=int, default=5, help='Number of results (default: 5)')
    parser.add_argument('--mode', choices=['standard', 'strict', 'relaxed'], default='standard',
                      help='Search mode (default: standard)')
    
    args = parser.parse_args()
    
    success = test_local_search(args.query, args.top_k, args.mode)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())

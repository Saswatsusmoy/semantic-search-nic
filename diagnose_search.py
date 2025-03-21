"""
Diagnostic script to check each component of the search pipeline
"""
import os
import json
import logging
import argparse
import numpy as np
import traceback
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def diagnose_search_pipeline(query="bakery", json_path="output.json"):
    """
    Run diagnostics on the entire search pipeline
    
    Args:
        query: Test search query
        json_path: Path to JSON data file
    """
    logger.info(f"Starting search pipeline diagnostics with query: '{query}'")
    
    # Step 1: Check if JSON file exists and has embeddings
    logger.info("\n=== Step 1: Check JSON data ===")
    
    if not os.path.exists(json_path):
        logger.error(f"JSON file not found: {json_path}")
        return False
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        logger.info(f"JSON data loaded: {len(data)} documents")
        
        # Check for Vector-Embedding_SubClass fields
        embedding_count = sum(1 for doc in data if "Vector-Embedding_SubClass" in doc and isinstance(doc["Vector-Embedding_SubClass"], list))
        logger.info(f"Documents with embeddings: {embedding_count} ({embedding_count/len(data)*100:.2f}%)")
        
        if embedding_count == 0:
            logger.error("No documents have embeddings - search will not work!")
            logger.info("Please run the data processing to generate embeddings.")
            return False
    except Exception as e:
        logger.error(f"Error loading JSON data: {str(e)}")
        logger.error(traceback.format_exc())
        return False
    
    # Step 2: Check embeddings model
    logger.info("\n=== Step 2: Check embeddings model ===")
    try:
        from vector_embeddings_manager import cached_get_embedding
        
        start_time = time.time()
        embedding = cached_get_embedding(query, model_name='all-MiniLM-L6-v2')
        duration = time.time() - start_time
        
        logger.info(f"Generated embedding in {duration:.2f} seconds")
        logger.info(f"Embedding dimension: {len(embedding)}")
        logger.info(f"First 5 values: {embedding[:5]}")
    except Exception as e:
        logger.error(f"Error generating embedding: {str(e)}")
        logger.error(traceback.format_exc())
        return False
    
    # Step 3: Check FAISS index
    logger.info("\n=== Step 3: Check FAISS index ===")
    try:
        from faiss_index_manager import FAISSIndexManager
        
        index_manager = FAISSIndexManager(json_file_path=json_path)
        
        # Check existing index
        index_path = index_manager.index_path
        id_map_path = index_manager.id_map_path
        
        logger.info(f"Index path: {index_path}")
        logger.info(f"ID map path: {id_map_path}")
        
        if os.path.exists(index_path) and os.path.exists(id_map_path):
            logger.info("Index files exist")
            
            # Try loading the index
            if index_manager.load_index():
                logger.info(f"Successfully loaded index with {index_manager.index.ntotal} vectors")
                logger.info(f"ID map size: {len(index_manager.id_map)}")
            else:
                logger.warning("Could not load existing index - will need to build it")
        else:
            logger.warning("Index files don't exist - need to build index")
        
        # Try building index
        logger.info("Testing index build...")
        if index_manager.build_index(force_rebuild=True):
            logger.info("Successfully built index")
            logger.info(f"Index contains {index_manager.index.ntotal} vectors")
        else:
            logger.error("Failed to build index")
            return False
        
        # Try search
        logger.info(f"Testing search for query: '{query}'")
        query_embedding = cached_get_embedding(query, model_name='all-MiniLM-L6-v2')
        
        search_results = index_manager.search(query_embedding, top_k=5)
        logger.info(f"Search returned {len(search_results)} results")
        
        if len(search_results) > 0:
            for i, (doc_id, score) in enumerate(search_results):
                logger.info(f"Result {i+1}: ID={doc_id}, Score={score:.4f}")
        else:
            logger.warning("No search results found")
            
    except Exception as e:
        logger.error(f"Error checking FAISS index: {str(e)}")
        logger.error(traceback.format_exc())
        return False
    
    # Step 4: Test the full API search
    logger.info("\n=== Step 4: Check API search ===")
    try:
        import requests
        import time
        
        # Start the API server if it's not running
        # (this would be implementation-dependent)
        
        # Make a test request
        test_data = {
            "query": query,
            "result_count": 5,
            "search_mode": "relaxed",
            "show_metrics": True
        }
        
        logger.info("Note: This test requires the API server to be running.")
        logger.info("If the API is running on a different port/host, adjust the URL.")
        
        try:
            response = requests.post("http://localhost:8000/search", json=test_data, timeout=10)
            
            if response.ok:
                result_data = response.json()
                logger.info(f"API search successful: {len(result_data.get('results', []))} results")
                logger.info(f"Metrics: {json.dumps(result_data.get('metrics', {}), indent=2)}")
            else:
                logger.warning(f"API search failed with status {response.status_code}: {response.text}")
        except requests.exceptions.ConnectionError:
            logger.warning("Could not connect to API server - make sure it's running")
        except Exception as e:
            logger.warning(f"API test error: {str(e)}")
    except ImportError:
        logger.warning("Requests library not available - skipping API test")
    
    logger.info("\n=== Diagnostics completed ===")
    return True

if __name__ == "__main__":
    import time
    import sys
    
    parser = argparse.ArgumentParser(description="Diagnose search pipeline")
    parser.add_argument("--query", "-q", default="bakery", help="Test search query")
    parser.add_argument("--json", "-j", default="output.json", help="Path to JSON data file")
    
    args = parser.parse_args()
    
    success = diagnose_search_pipeline(args.query, args.json)
    sys.exit(0 if success else 1)

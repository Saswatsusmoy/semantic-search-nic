"""
Debug script to test the search functionality directly
"""

import os
import sys
import json
import time
import logging
import traceback
from dotenv import load_dotenv
from pymongo import MongoClient
from bson import ObjectId
import numpy as np

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def test_mongodb_connection():
    """Test MongoDB connection and get collection info"""
    try:
        mongo_uri = os.environ.get("MONGO_URI")
        db_name = os.environ.get("DB_NAME", "NIC_Database")
        collection_name = os.environ.get("COLLECTION_NAME", "NIC_Codes")
        
        if not mongo_uri:
            logger.error("MONGO_URI not set in environment variables or .env file")
            return False
            
        client = MongoClient(mongo_uri)
        db = client[db_name]
        collection = db[collection_name]
        
        # Test connection by getting collection stats
        count = collection.count_documents({})
        logger.info(f"Connected to MongoDB. Collection '{collection_name}' has {count} documents.")
        
        # Get sample document
        sample_doc = collection.find_one()
        if sample_doc:
            logger.info(f"Sample document fields: {list(sample_doc.keys())}")
        
        client.close()
        return True
    except Exception as e:
        logger.error(f"MongoDB connection error: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def test_faiss_index():
    """Test FAISS index loading and basic search"""
    try:
        # Import here to avoid issues with module loading
        from faiss_index_manager import FAISSIndexManager
        from vector_embeddings_manager import cached_get_embedding
        
        # Initialize FAISS manager
        mongo_uri = os.environ.get("MONGO_URI")
        db_name = os.environ.get("DB_NAME", "NIC_Database")
        collection_name = os.environ.get("COLLECTION_NAME", "NIC_Codes")
        
        faiss_manager = FAISSIndexManager(mongo_uri, db_name, collection_name)
        
        # Check if index exists and is loaded
        logger.info(f"FAISS index path: {faiss_manager.index_path}")
        logger.info(f"FAISS ID map path: {faiss_manager.id_map_path}")
        
        index_exists = os.path.exists(faiss_manager.index_path)
        id_map_exists = os.path.exists(faiss_manager.id_map_path)
        
        logger.info(f"Index file exists: {index_exists}")
        logger.info(f"ID map file exists: {id_map_exists}")
        
        # Load the index
        load_success = faiss_manager.load_index()
        logger.info(f"Index loaded successfully: {load_success}")
        
        if load_success:
            # Get index stats
            logger.info(f"Index dimensions: {faiss_manager.index.d}")
            logger.info(f"Index size (vectors): {faiss_manager.index.ntotal}")
            logger.info(f"ID map size: {len(faiss_manager.id_map) if faiss_manager.id_map else 'N/A'}")
            
            # Test search
            test_query = "software development"
            logger.info(f"Testing search with query: '{test_query}'")
            
            # Get embedding
            embedding = cached_get_embedding(test_query, 'all-MiniLM-L6-v2')
            logger.info(f"Embedding generated: shape={np.array(embedding).shape}")
            
            # Perform search
            search_results = faiss_manager.search(embedding, top_k=5)
            logger.info(f"Search returned {len(search_results)} results")
            
            if search_results:
                for i, (doc_id, similarity) in enumerate(search_results[:5]):
                    logger.info(f"Result {i+1}: ID={doc_id}, Similarity={similarity:.4f}")
                    
                # Test retrieving docs from MongoDB
                client = MongoClient(mongo_uri)
                db = client[db_name]
                collection = db[collection_name]
                
                doc_ids = [ObjectId(doc_id) for doc_id, _ in search_results[:3]]
                docs = list(collection.find({"_id": {"$in": doc_ids}}))
                
                logger.info(f"Retrieved {len(docs)} documents from MongoDB")
                client.close()
            
        return load_success
    except Exception as e:
        logger.error(f"FAISS index test error: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def main():
    """Run all tests"""
    print("-" * 50)
    print("MongoDB Connection Test")
    print("-" * 50)
    mongo_success = test_mongodb_connection()
    print(f"MongoDB test {'PASSED' if mongo_success else 'FAILED'}")
    
    print("\n" + "-" * 50)
    print("FAISS Index Test")
    print("-" * 50)
    faiss_success = test_faiss_index()
    print(f"FAISS index test {'PASSED' if faiss_success else 'FAILED'}")
    
    return 0 if mongo_success and faiss_success else 1

if __name__ == "__main__":
    sys.exit(main())

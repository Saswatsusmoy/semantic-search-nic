"""
Debug helper tool for semantic search application.
Run this script to diagnose common issues with MongoDB connection and data.
"""

import pymongo
from pymongo import MongoClient
import numpy as np
import json
import sys
import logging
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_mongodb_connection():
    """Test connection to MongoDB Atlas"""
    try:
        connection_string = os.environ.get("MONGO_URI")
        if not connection_string:
            logger.error("MongoDB connection string not found in environment variables")
            return None
            
        logger.info(f"Testing connection to MongoDB Atlas...")
        client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        logger.info("✓ MongoDB connection successful!")
        return client
    except Exception as e:
        logger.error(f"✗ MongoDB connection failed: {str(e)}")
        return None

def check_database_and_collection(client):
    """Check if database and collection exist"""
    if not client:
        return
    
    try:
        database_name = "NIC_Database"
        collection_name = "NIC_Codes"
        
        # Get list of database names
        database_names = client.list_database_names()
        if database_name not in database_names:
            logger.error(f"✗ Database '{database_name}' not found. Available databases: {database_names}")
            return None
        
        db = client[database_name]
        collection_names = db.list_collection_names()
        if collection_name not in collection_names:
            logger.error(f"✗ Collection '{collection_name}' not found. Available collections: {collection_names}")
            return None
        
        logger.info(f"✓ Database '{database_name}' and collection '{collection_name}' exist")
        return db[collection_name]
    except Exception as e:
        logger.error(f"✗ Error checking database and collection: {str(e)}")
        return None

def check_documents_with_embeddings(collection):
    """Check if documents have embeddings"""
    if not collection:
        return
    
    try:
        # Count total documents
        total_docs = collection.count_documents({})
        logger.info(f"Total documents in collection: {total_docs}")
        
        # Count documents with embeddings
        docs_with_embeddings = collection.count_documents({"Vector-Embedding_SubClass": {"$exists": True}})
        logger.info(f"Documents with embeddings: {docs_with_embeddings}")
        
        if docs_with_embeddings == 0:
            logger.error("✗ No documents have vector embeddings!")
            return
        
        # Get a sample document with embeddings
        sample_doc = collection.find_one({"Vector-Embedding_SubClass": {"$exists": True}})
        if sample_doc:
            # Check embedding format
            embedding = sample_doc.get("Vector-Embedding_SubClass")
            if not embedding:
                logger.error("✗ Empty embedding found")
            elif not isinstance(embedding, list):
                logger.error(f"✗ Embedding is not a list but {type(embedding)}")
            else:
                logger.info(f"✓ Sample embedding looks good: list with {len(embedding)} dimensions")
                
            # Check for field names that might be problematic
            for field in ["NIC", "NIC_Code", "Section", "Divison", "Division", "Group", "Class", "Sub-Class"]:
                if field in sample_doc:
                    logger.info(f"✓ Field '{field}' exists in documents")
                else:
                    logger.warning(f"? Field '{field}' not found in sample document")
                
            # Verify JSON serialization
            try:
                # Remove _id field which isn't JSON serializable
                sample_doc.pop("_id", None)
                json.dumps(sample_doc)
                logger.info("✓ Document is JSON serializable")
            except (TypeError, ValueError) as e:
                logger.error(f"✗ Document is not JSON serializable: {str(e)}")
                # Try to identify problematic fields
                for key, value in sample_doc.items():
                    try:
                        json.dumps({key: value})
                    except (TypeError, ValueError):
                        logger.error(f"  - Problem field: '{key}' with type {type(value)}")
    except Exception as e:
        logger.error(f"✗ Error checking documents: {str(e)}")

def main():
    """Run all diagnostic checks"""
    logger.info("=== Semantic Search Diagnostic Tool ===")
    
    # Test MongoDB connection
    client = test_mongodb_connection()
    if not client:
        logger.error("MongoDB connection test failed. Fix connection issues before proceeding.")
        return
    
    # Check database and collection
    collection = check_database_and_collection(client)
    if not collection:
        logger.error("Database/collection check failed.")
        return
    
    # Check documents with embeddings
    check_documents_with_embeddings(collection)
    
    # Close connection
    client.close()
    logger.info("=== Diagnostic complete ===")

if __name__ == "__main__":
    main()

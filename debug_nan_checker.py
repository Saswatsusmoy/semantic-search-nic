"""
Utility script to check for 'nan' values in Sub-Class field and optionally remove them.
"""

import pymongo
from pymongo import MongoClient
import logging
import argparse
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def connect_to_mongodb():
    """Connect to MongoDB Atlas"""
    try:
        connection_string = os.environ.get("MONGO_URI")
        if not connection_string:
            logger.error("MongoDB connection string not found in environment variables")
            return None
            
        logger.info(f"Connecting to MongoDB Atlas...")
        client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        logger.info("MongoDB connection successful!")
        return client
    except Exception as e:
        logger.error(f"MongoDB connection failed: {str(e)}")
        return None

def check_nan_values(client, fix=False):
    """
    Check for 'nan' values in Sub-Class field
    
    Args:
        client: MongoDB client
        fix (bool): If True, updates documents with 'nan' to have empty Sub-Class
    """
    try:
        db = client["NIC_Database"]
        collection = db["NIC_Codes"]
        
        # Count total documents
        total_docs = collection.count_documents({})
        logger.info(f"Total documents in collection: {total_docs}")
        
        # Find documents where Sub-Class is "nan"
        nan_query = {"Sub-Class": "nan"}
        nan_docs = list(collection.find(nan_query))
        logger.info(f"Found {len(nan_docs)} documents with Sub-Class = 'nan'")
        
        # Find documents where Sub-Class is empty string
        empty_query = {"Sub-Class": ""}
        empty_docs = list(collection.find(empty_query))
        logger.info(f"Found {len(empty_docs)} documents with Sub-Class = ''")
        
        # Find documents where Sub-Class doesn't exist
        null_query = {"Sub-Class": {"$exists": False}}
        null_docs = list(collection.find(null_query))
        logger.info(f"Found {len(null_docs)} documents without Sub-Class field")
        
        # Check for other potential bad values
        bad_values = ["n/a", "na", "none", "null", "undefined"]
        for val in bad_values:
            count = collection.count_documents({"Sub-Class": val})
            if count > 0:
                logger.info(f"Found {count} documents with Sub-Class = '{val}'")
        
        # Fix nan values if requested
        if fix and nan_docs:
            logger.info(f"Fixing {len(nan_docs)} documents with Sub-Class = 'nan'...")
            result = collection.update_many(
                {"Sub-Class": "nan"},
                {"$set": {"Sub-Class": ""}}
            )
            logger.info(f"Updated {result.modified_count} documents")
            
    except Exception as e:
        logger.error(f"Error checking documents: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check for 'nan' values in Sub-Class field")
    parser.add_argument('--fix', action='store_true', help='Fix nan values by changing them to empty strings')
    args = parser.parse_args()
    
    client = connect_to_mongodb()
    if client:
        try:
            check_nan_values(client, fix=args.fix)
        finally:
            client.close()
            logger.info("MongoDB connection closed")
    else:
        logger.error("Failed to connect to MongoDB")

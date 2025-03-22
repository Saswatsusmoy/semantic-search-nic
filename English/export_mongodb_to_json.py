"""
Script to export all data from MongoDB Atlas to a JSON file
"""

import os
import json
import logging
from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Custom JSON encoder to handle MongoDB ObjectId
class MongoJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)

def connect_to_mongodb():
    """Connect to MongoDB Atlas"""
    try:
        connection_string = os.environ.get("MONGO_URI")
        if not connection_string:
            logger.error("MongoDB connection string not found in environment variables")
            logger.error("Please set MONGO_URI in your .env file")
            return None
            
        logger.info(f"Connecting to MongoDB Atlas...")
        client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        logger.info("MongoDB connection successful!")
        return client
    except Exception as e:
        logger.error(f"MongoDB connection failed: {str(e)}")
        return None

def export_data_to_json(output_file="mongodb_export.json"):
    """
    Export all data from MongoDB to a JSON file
    
    Args:
        output_file (str): Path to the output JSON file
    """
    # Connect to MongoDB
    client = connect_to_mongodb()
    if not client:
        return False
    
    try:
        # Get database and collection names from environment
        db_name = os.environ.get("DB_NAME", "NIC_Database")
        collection_name = os.environ.get("COLLECTION_NAME", "NIC_Codes")
        
        # Get the collection
        db = client[db_name]
        collection = db[collection_name]
        
        # Count documents
        total_docs = collection.count_documents({})
        logger.info(f"Found {total_docs} documents in {db_name}.{collection_name}")
        
        # Fetch all documents
        logger.info("Fetching all documents...")
        all_documents = list(collection.find({}))
        
        # Write to JSON file
        logger.info(f"Writing data to {output_file}...")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_documents, f, cls=MongoJSONEncoder, ensure_ascii=False, indent=2)
        
        logger.info(f"Successfully exported {len(all_documents)} documents to {output_file}")
        return True
    except Exception as e:
        logger.error(f"Error exporting data: {str(e)}")
        return False
    finally:
        logger.info("Closing MongoDB connection")
        client.close()

def main():
    # Ask for output file name or use default
    output_file = input("Enter output JSON file path (default: mongodb_export.json): ").strip()
    if not output_file:
        output_file = "mongodb_export.json"
    
    # Make sure the output directory exists
    output_dir = os.path.dirname(os.path.abspath(output_file))
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Export data
    success = export_data_to_json(output_file)
    
    if success:
        logger.info("Export completed successfully!")
    else:
        logger.error("Export failed!")

if __name__ == "__main__":
    main()

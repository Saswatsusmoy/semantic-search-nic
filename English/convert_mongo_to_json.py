"""
Utility script to convert MongoDB documents to a local JSON file
"""

import os
import sys
import json
import logging
import argparse
from dotenv import load_dotenv
from pymongo import MongoClient

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def convert_mongodb_to_json(output_path="output.json", limit=None):
    """
    Convert MongoDB documents to a local JSON file
    
    Args:
        output_path: Path to save the JSON file
        limit: Maximum number of documents to fetch (None for all)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get MongoDB connection details from environment variables
        mongo_uri = os.environ.get("MONGO_URI")
        db_name = os.environ.get("DB_NAME", "NIC_Database")
        collection_name = os.environ.get("COLLECTION_NAME", "NIC_Codes")
        
        if not mongo_uri:
            logger.error("MONGO_URI not set in environment variables or .env file")
            return False
        
        # Connect to MongoDB
        client = MongoClient(mongo_uri)
        db = client[db_name]
        collection = db[collection_name]
        
        # Fetch documents
        if limit:
            cursor = collection.find().limit(limit)
        else:
            cursor = collection.find()
        
        # Convert to list and prepare for JSON serialization
        documents = []
        for doc in cursor:
            # Convert ObjectId to string
            doc["_id"] = str(doc["_id"])
            documents.append(doc)
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(documents, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Successfully exported {len(documents)} documents to {output_path}")
        client.close()
        return True
        
    except Exception as e:
        logger.error(f"Error converting MongoDB to JSON: {str(e)}")
        return False

def main():
    """
    Main function to parse command-line arguments and run the conversion
    """
    parser = argparse.ArgumentParser(description='Convert MongoDB data to local JSON file')
    parser.add_argument('--output', default='output.json', help='Output file path (default: output.json)')
    parser.add_argument('--limit', type=int, default=None, help='Limit number of documents (default: no limit)')
    
    args = parser.parse_args()
    
    success = convert_mongodb_to_json(args.output, args.limit)
    if success:
        print(f"Successfully converted MongoDB data to {args.output}")
        return 0
    else:
        print("Failed to convert MongoDB data to JSON")
        return 1

if __name__ == "__main__":
    sys.exit(main())

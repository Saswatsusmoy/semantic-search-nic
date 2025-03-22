import pymongo
import pandas as pd
import logging
from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def connect_to_mongodb():
    """
    Connect to MongoDB Atlas and return the collection object.
    """
    try:
        # MongoDB Atlas connection parameters from environment variables
        connection_string = os.environ.get("MONGO_URI")
        if not connection_string:
            logger.error("MongoDB connection string not found in environment variables")
            logger.error("Please set MONGO_URI in your .env file")
            return None
            
        database_name = os.environ.get("DB_NAME", "NIC_Database")
        collection_name = os.environ.get("COLLECTION_NAME", "NIC_Codes")
        
        # Connect to MongoDB Atlas
        client = MongoClient(connection_string)
        db = client[database_name]
        collection = db[collection_name]
        logger.info(f"Successfully connected to MongoDB Atlas: {database_name}.{collection_name}")
        return collection
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB Atlas: {str(e)}")
        raise

def merge_inclusions(collection):
    """
    Fetch documents, merge Inclusion from Exclusion into Description,
    and update the documents in MongoDB.
    """
    try:
        # Only fetch the fields we need
        projection = {"Description": 1, "Inclusion from Exclusion": 1}
        
        # Get all documents
        documents = list(collection.find({}, projection))
        logger.info(f"Found {len(documents)} documents in collection")
        
        update_count = 0
        for doc in documents:
            # Check if Inclusion from Exclusion exists and is not null/empty
            if "Inclusion from Exclusion" in doc and doc["Inclusion from Exclusion"] is not None:
                inclusion_text = doc["Inclusion from Exclusion"]
                
                # Convert to string if not already, handle NaN values
                if isinstance(inclusion_text, float) and pd.isna(inclusion_text):
                    continue
                
                inclusion_text = str(inclusion_text).strip()
                if not inclusion_text:
                    continue
                
                # Get original description or empty string if not present
                original_desc = ""
                if "Description" in doc and doc["Description"] is not None:
                    if isinstance(doc["Description"], float) and pd.isna(doc["Description"]):
                        original_desc = ""
                    else:
                        original_desc = str(doc["Description"]).strip()
                
                # Skip if Description already contains the inclusion text
                if original_desc and inclusion_text in original_desc:
                    continue
                
                # Create new description by appending inclusion text
                new_desc = original_desc
                if new_desc:
                    new_desc += "\n\nInclusions: " + inclusion_text
                else:
                    new_desc = "Inclusions: " + inclusion_text
                
                # Update document using _id as identifier (MongoDB's default unique identifier)
                collection.update_one(
                    {"_id": doc["_id"]},
                    {"$set": {"Description": new_desc}}
                )
                update_count += 1
        
        logger.info(f"Updated {update_count} documents with inclusion data")
        return update_count
    except Exception as e:
        logger.error(f"Error while merging inclusions: {str(e)}")
        raise

def main():
    try:
        # Connect to MongoDB Atlas
        collection = connect_to_mongodb()
        if collection is None:
            logger.error("No collection found. Exiting script.")
            return
        
        # Perform the merge operation
        updated_count = merge_inclusions(collection)
        
        logger.info(f"Script completed successfully. Total documents updated: {updated_count}")
    except Exception as e:
        logger.error(f"Script failed: {str(e)}")

if __name__ == "__main__":
    main()

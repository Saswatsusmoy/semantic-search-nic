import pandas as pd
from pymongo import MongoClient
import sys
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# MongoDB Atlas connection string from environment variable
MONGO_CONNECTION_STRING = os.environ.get("MONGO_URI")
DATABASE_NAME = os.environ.get("DB_NAME", "NIC_Database")
COLLECTION_NAME = os.environ.get("COLLECTION_NAME", "NIC_Codes")

def read_excel_file(file_path):
    """Read Excel file and return as a list of dictionaries"""
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            sys.exit(1)
        
        # Read the Excel file
        logger.info(f"Reading Excel file: {file_path}")
        df = pd.read_excel(file_path)
        
        # Convert to list of dictionaries (records)
        records = df.to_dict(orient='records')
        logger.info(f"Successfully parsed {len(records)} records from Excel")
        return records
    except Exception as e:
        logger.error(f"Error reading Excel file: {e}")
        sys.exit(1)

def connect_to_mongodb():
    """Connect to MongoDB Atlas and return database connection"""
    try:
        if not MONGO_CONNECTION_STRING:
            logger.error("MongoDB connection string not found in environment variables")
            logger.error("Please set MONGO_URI in your .env file")
            sys.exit(1)
        
        logger.info("Connecting to MongoDB Atlas...")
        client = MongoClient(MONGO_CONNECTION_STRING)
        # Test the connection
        client.admin.command('ping')
        logger.info("Successfully connected to MongoDB Atlas")
        return client[DATABASE_NAME]
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        sys.exit(1)

def insert_data_to_mongodb(db, collection_name, data):
    """Insert data into MongoDB collection"""
    try:
        collection = db[collection_name]
        result = collection.insert_many(data)
        logger.info(f"Successfully inserted {len(result.inserted_ids)} documents into MongoDB")
        return result.inserted_ids
    except Exception as e:
        logger.error(f"Error inserting data into MongoDB: {e}")
        sys.exit(1)

def main():
    # Define the Excel file path - get from environment or prompt user
    excel_file_path = os.environ.get("DEFAULT_INPUT_FILE")
    
    if not excel_file_path or not os.path.exists(excel_file_path):
        excel_file_path = input("Enter the path to your Excel file: ")
    
    # Read Excel data
    data = read_excel_file(excel_file_path)
    
    # Connect to MongoDB
    db = connect_to_mongodb()
    
    # Insert data into MongoDB
    insert_data_to_mongodb(db, COLLECTION_NAME, data)
    
    logger.info("Data migration completed successfully!")

if __name__ == "__main__":
    main()

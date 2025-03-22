import os
import pymongo
from dotenv import load_dotenv
import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
from faiss_index_manager import FAISSIndexManager

# Load environment variables from .env file
load_dotenv()

# Get MongoDB connection string from environment variable
MONGO_URI = os.environ.get("MONGO_URI")
if not MONGO_URI:
    raise ValueError("MONGO_URI not set in environment variables. Please create a .env file with your MongoDB connection string.")

DB_NAME = os.environ.get("DB_NAME", "NIC_Database")
COLLECTION_NAME = os.environ.get("COLLECTION_NAME", "NIC_Codes")

# Load a pre-trained sentence transformer model for generating embeddings
# This model will convert text descriptions into vector embeddings
print("Loading sentence transformer model...")
model = SentenceTransformer('all-MiniLM-L6-v2')  # A good general-purpose model for embeddings

def connect_to_mongodb():
    """Establish connection to MongoDB Atlas"""
    try:
        client = pymongo.MongoClient(MONGO_URI)
        # Verify connection
        client.admin.command('ping')
        print("Successfully connected to MongoDB!")
        return client
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")
        raise

def get_documents_with_subclass(db):
    """Fetch all documents with non-null Sub-Class field"""
    collection = db[COLLECTION_NAME]
    # Find documents where "Sub-Class" exists and is not null
    query = {"Sub-Class": {"$exists": True, "$ne": None}}
    # Get only the required fields
    projection = {"_id": 1, "Sub-Class": 1, "Description": 1}
    
    documents = list(collection.find(query, projection))
    print(f"Found {len(documents)} documents with non-null Sub-Class")
    return documents

def generate_embeddings(descriptions):
    """
    Generate embeddings for a list of descriptions using Sentence-BERT.
    This creates a vector representation of each complete description,
    not individual words.
    """
    # Handle potential None values in descriptions and convert floats to strings
    valid_descriptions = []
    for desc in descriptions:
        if desc is None:
            valid_descriptions.append("")
        elif isinstance(desc, float):
            valid_descriptions.append(str(desc) if not np.isnan(desc) else "")
        else:
            valid_descriptions.append(str(desc))
    
    # Print some stats about the descriptions
    num_empty = sum(1 for desc in valid_descriptions if not desc.strip())
    print(f"Generating embeddings for {len(valid_descriptions)} descriptions ({num_empty} empty)")
    
    # Generate embeddings for the entire descriptions at once
    # This creates semantic vector representations of each description as a whole
    embeddings = model.encode(valid_descriptions, show_progress_bar=True)
    
    print(f"Generated {len(embeddings)} embeddings with dimensionality {embeddings[0].shape[0]}")
    return embeddings

def update_documents_with_embeddings(db, documents, embeddings):
    """Update MongoDB documents with their corresponding embeddings"""
    collection = db[COLLECTION_NAME]
    update_count = 0
    
    print("Updating documents with embeddings...")
    for doc, embedding in tqdm(zip(documents, embeddings), total=len(documents)):
        # Convert numpy array to list for MongoDB storage
        embedding_list = embedding.tolist()
        
        # Update the document with the embedding
        result = collection.update_one(
            {"_id": doc["_id"]},
            {"$set": {"Vector-Embedding_SubClass": embedding_list}}
        )
        
        if result.modified_count > 0:
            update_count += 1
    
    print(f"Updated {update_count} documents with embeddings")

def main():
    # Connect to MongoDB
    client = connect_to_mongodb()
    db = client[DB_NAME]
    
    # Get documents with non-null Sub-Class
    documents = get_documents_with_subclass(db)
    
    if not documents:
        print("No documents found with non-null Sub-Class field")
        return
    
    # Extract descriptions - these are complete text fields, not individual words
    descriptions = [doc.get("Description", "") for doc in documents]
    print(f"Sample description: '{str(descriptions[0])[:100]}...'")
    
    # Generate embeddings for the entire descriptions
    print("Generating document embeddings using Sentence-BERT...")
    embeddings = generate_embeddings(descriptions)
    
    # Update documents with embeddings
    update_documents_with_embeddings(db, documents, embeddings)
    
    # Build FAISS index with the new embeddings
    print("Building FAISS index with the generated embeddings...")
    faiss_manager = FAISSIndexManager(MONGO_URI)
    success = faiss_manager.build_index(force_rebuild=True)
    
    if success:
        print("FAISS index built successfully with cosine similarity!")
    else:
        print("Failed to build FAISS index.")
    
    print("Process completed successfully!")
    client.close()

if __name__ == "__main__":
    main()

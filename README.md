# Semantic Search for NIC Codes

![FAISS Powered](https://img.shields.io/badge/Powered%20by-FAISS-blue)
![MongoDB Atlas](https://img.shields.io/badge/Database-MongoDB%20Atlas-green)
![Python](https://img.shields.io/badge/Language-Python%203.7+-orange)

A high-performance semantic search application for National Industrial Classification (NIC) codes using Facebook AI Similarity Search (FAISS) and MongoDB Atlas.

## 📋 Overview

This application provides an intuitive interface for searching India's National Industrial Classification codes using natural language queries. Rather than requiring exact keyword matches, users can describe business activities in plain language, and the system uses AI-powered semantic search to find the most relevant industry classifications.

## ✨ Features

- **Natural Language Search**: Describe industries or business activities in everyday language
- **AI-Powered Semantic Matching**: Using sentence embeddings and FAISS for highly accurate results
- **High Performance**: FAISS vector similarity search is orders of magnitude faster than traditional methods
- **Hierarchical Results**: View the complete NIC code hierarchy (Section → Division → Group → Class → Sub-Class)
- **User-Friendly Interface**: Clean, modern UI with expandable result cards
- **Advanced Options**: Configure search parameters for more precise results

## 🔍 How It Works

1. **Vector Embeddings**: The application uses the `sentence-transformers` model to convert text descriptions into high-dimensional vectors
2. **FAISS Indexing**: These vectors are stored in a FAISS index for lightning-fast similarity search
3. **Query Processing**: When you enter a search query, it's converted to a vector using the same model
4. **Similarity Search**: FAISS finds the most similar vectors in the database in milliseconds
5. **Result Ranking**: Results are ranked by similarity score and displayed in a user-friendly format

## 📚 Technical Architecture

- **Frontend**: HTML, CSS, JavaScript with Bootstrap 5
- **Backend**: Python Flask server
- **Embeddings**: Sentence-Transformers with all-MiniLM-L6-v2 model
- **Vector Database**: FAISS (Facebook AI Similarity Search)
- **Document Database**: MongoDB Atlas
- **Search Algorithm**: L2 distance-based nearest neighbor search

## 🛠️ Installation and Setup

### Prerequisites

- Python 3.7 or higher
- MongoDB Atlas account (or local MongoDB installation)
- Git (optional)

### Step 1: Get the Code

Clone the repository or download the source code:

```bash
git clone <repository-url>
cd semantic-search-nic
```

### Step 2: Create a Virtual Environment

```bash
# Create a virtual environment
python -m venv venv

# Activate it (Windows)
venv\Scripts\activate

# Activate it (macOS/Linux)
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

Create a `.env` file in the project root directory with your MongoDB connection details:

```env
MONGO_URI="mongodb+srv://username:password@your-cluster.mongodb.net/"
```

### Step 5: Generate or Update Vector Embeddings

If you're starting with a new database, run:

```bash
python vector_embeddings_subclasses.py
```

This will create embeddings for all documents in your database and build the FAISS index.

### Step 6: Run the Application

```bash
python semantic_search_app.py
```

Navigate to `http://127.0.0.1:5000/` in your browser to use the application.

## 🔄 Using FAISS for Semantic Search

FAISS (Facebook AI Similarity Search) is a library that enables efficient similarity search for dense vectors. Our implementation uses:

- **IndexFlatL2**: A flat index that computes exact L2 distances between vectors
- **IndexIDMap**: A wrapper that maps external IDs (MongoDB ObjectIDs) to internal FAISS indices
- **Disk Persistence**: The index is saved to disk for faster startup times
- **On-the-fly Index Building**: If no index exists, one is created automatically

### Advantages over Traditional Cosine Similarity

- **Speed**: FAISS is optimized for high-dimensional vector search and scales to millions of records
- **Memory Efficiency**: More efficient memory usage than naive implementations
- **GPU Support**: Can leverage GPU acceleration for even faster search (requires faiss-gpu)
- **Advanced Indexing**: Supports approximate nearest neighbor algorithms for sub-millisecond searches

## 🧠 Admin Features

Access the admin panel by clicking "Admin" in the footer:

- **Rebuild Index**: Manually rebuild the FAISS index if you've updated the database
- **Index Statistics**: View information about the current FAISS index (size, dimensions, etc.)

## 📊 Performance Considerations

- The initial loading of the FAISS index takes a few seconds
- Search queries typically return in under 100ms
- The application is optimized for a collection size of up to ~100,000 documents

## 🔧 Troubleshooting

- **Index not building**: Ensure your MongoDB has documents with the `Vector-Embedding_SubClass` field
- **Connection errors**: Check your MongoDB Atlas connection string and network connectivity
- **Slow search**: The first search might be slower as the model loads; subsequent searches should be faster

## 📱 API Documentation

The application provides a simple REST API endpoint:

- **POST /search**: Submit a search query
  - Request body: `query` (string) - The natural language query
  - Response: JSON array of matching results with similarity scores

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Facebook Research for creating FAISS
- Sentence-Transformers team for their excellent embeddings models
- MongoDB Atlas for vector database capabilities

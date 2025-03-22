# Semantic Search for NIC Codes

![FAISS Powered](https://img.shields.io/badge/Powered%20by-FAISS-blue)
![JSON Data](https://img.shields.io/badge/Data-Local%20JSON-green)
![Python](https://img.shields.io/badge/Language-Python%203.7+-orange)

A high-performance semantic search application for National Industrial Classification (NIC) codes using Facebook AI Similarity Search (FAISS) and local JSON data storage.

## 📋 Overview

This application provides semantic (meaning-based) search functionality for National Industrial Classification (NIC) codes. Unlike traditional keyword search, it understands the meaning behind search queries, delivering more relevant and intuitive results.

## ✨ Features

- **Semantic Search**: Finds relevant results based on meaning, not just keywords
- **Multiple Search Modes**: Standard, Strict, and Relaxed modes for different search precision needs
- **High Performance**: Fast search results using FAISS vector similarity
- **Local Data**: Uses a local JSON file for data storage without requiring a database connection
- **Admin Features**: Tools to manage the search index and view statistics
- **REST API**: Simple API for integration with other applications

## 🔍 How It Works

1. **Embedding Generation**: Search queries and NIC descriptions are converted to vector embeddings using a pre-trained language model (all-MiniLM-L6-v2)
2. **Similarity Search**: FAISS finds NIC codes with the most similar vector representations to the query
3. **Result Ranking**: Results are ranked by similarity score and returned to the user

## 📚 Technical Architecture

- **Frontend**: Simple HTML/CSS/JS interface
- **Backend**: Flask web application
- **Embeddings**: SentenceTransformer (all-MiniLM-L6-v2)
- **Vector Search**: Facebook AI Similarity Search (FAISS) with cosine similarity
- **Data Storage**: Local JSON file (output.json)

## 🛠️ Installation and Setup

1. **Clone the repository**
   ```
   git clone https://github.com/yourusername/semantic-search-nic.git
   cd semantic-search-nic
   ```

2. **Create a virtual environment**
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```
   pip install -r requirements.txt
   ```

4. **Prepare your data**
   - Ensure your NIC code data is in a file named `output.json` in the project root
   - The JSON file should contain an array of objects with fields like Section, Division, Group, Class, Sub-Class, and Description

5. **Run the application**
   ```
   python semantic_search_app.py
   ```

6. **Access the application**
   - Open your browser and go to `http://localhost:5000`

## 🔄 Using FAISS for Semantic Search

The application automatically:
- Loads the FAISS index on startup if it exists
- Creates a new index if none exists
- Uses cosine similarity for semantic matching
- Optimizes search based on the selected mode (standard, strict, or relaxed)

To manually rebuild the index:
1. Access the admin section
2. Click "Rebuild Index"

## 🧠 Admin Features

Access the admin panel by clicking "Admin" in the footer:

- **Rebuild Index**: Manually rebuild the FAISS index if you've updated your data
- **Index Statistics**: View information about the current FAISS index (size, dimensions, etc.)

## 📊 Performance Considerations

- The initial loading of the FAISS index takes a few seconds
- Search queries typically return in under 100ms
- The application is optimized for a collection size of up to ~100,000 documents
- Search mode affects both result quality and performance:
  - Strict mode: Higher threshold (0.7), more precise results
  - Standard mode: Balanced threshold (0.5)
  - Relaxed mode: Lower threshold (0.3), more results but less precise

## 🔧 Troubleshooting

- **Index not building**: Ensure your `output.json` file exists and contains valid data
- **Missing fields in results**: Check that your JSON data includes all required fields
- **Slow search**: The first search might be slower as the model loads; subsequent searches should be faster

## 📱 API Documentation

The application provides a simple REST API endpoint:

- **POST /search**: Submit a search query
  - Request body: `query` (string) - The natural language query
  - Optional parameters: 
    - `result_count` (int, default=10) - Number of results to return
    - `search_mode` (string, default="standard") - "standard", "strict", or "relaxed" 
    - `show_metrics` (boolean, default=false) - Include performance metrics
  - Response: JSON array of matching results with similarity scores

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Facebook Research for creating FAISS
- Sentence-Transformers team for their excellent embeddings models

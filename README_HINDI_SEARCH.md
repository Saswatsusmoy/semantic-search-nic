# Hindi Semantic Search with FAISS

This project implements semantic search for Hindi documents using pre-computed embeddings stored in `output_hindi.json` and FAISS for efficient similarity search.

## Features

- Uses pre-computed embeddings from `output_hindi.json`
- FAISS index with cosine similarity for fast and accurate search
- Hindi embeddings using "krutrim-ai-labs/Vyakyarth" model for encoding search queries
- Command-line interface for easy usage
- Interactive search mode

## Requirements

Install the required packages:

```bash
pip install faiss-cpu transformers torch numpy
```

For GPU support (optional):

```bash
pip install faiss-gpu
```

## Usage

### Building the Index

First, build and save the FAISS index:

```bash
python search_hindi_cli.py --build-index --index hindi_faiss.index
```

### Basic Search

Search using a query:

```bash
python search_hindi_cli.py "गेहूं की खेती"
```

### Advanced Options

Search with custom parameters:

```bash
python search_hindi_cli.py "चावल उगाना" --top-k 10 --index hindi_faiss.index
```

### Interactive Mode

Start interactive search mode:

```bash
python search_hindi_cli.py
```

### JSON Output

Get results in JSON format:

```bash
python search_hindi_cli.py "फल उगाना" --json
```

## API Usage

You can also use the `HindiSemanticSearch` class in your own code:

```python
from hindi_semantic_search import HindiSemanticSearch

# Initialize with embeddings file
search = HindiSemanticSearch(embeddings_file="output_hindi.json")

# Or load a pre-built index
# search = HindiSemanticSearch(index_path="hindi_faiss.index")

# Search
results = search.search("अनाज की खेती", top_k=5)

# Process results
for result in results:
    print(f"Score: {result['score']}, Description: {result['document']['description']}")
```

## Notes

- The search works best for Hindi language queries
- Pre-computed embeddings must be available in the `output_hindi.json` file
- Building the index for the first time may take a few moments
- The model "krutrim-ai-labs/Vyakyarth" will be downloaded the first time you run a search

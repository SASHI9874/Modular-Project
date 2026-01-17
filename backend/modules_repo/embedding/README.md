# Text Embedder (Vector Generation)

## Overview

**Text Embedder** is a robust, production-grade module for converting raw text into high-dimensional vector embeddings.  
It is designed for **Retrieval-Augmented Generation (RAG)** applications, **semantic search**, and **text clustering** tasks.

Unlike simple embedding wrappers, this module automatically handles - 
**text chunking**, 
**memory optimization (lazy loading)**, and 
**hardware acceleration**, making it safe and efficient for real-world production systems.

---

##  Key Features

###  Smart Chunking
- Automatically splits large documents into smaller, overlapping segments
- Prevents hitting model token limits (e.g., 512 tokens)
- Improves retrieval accuracy by preserving context

###  Lazy Loading
- The AI model is **not loaded during initialization**
- Model loads only on the first `.run()` call
- Prevents memory spikes and server crashes during startup

###  Hardware Acceleration
- Automatically detects and uses available hardware:
  - **NVIDIA CUDA** (Linux / Windows)
  - **Apple MPS** (macOS M1 / M2)
- Falls back to **CPU** if no accelerator is available
- Can achieve up to **50× faster processing**

###  Structured Output
- Returns embeddings along with the corresponding text chunks
- Ready for direct insertion into vector databases:
  - **Chroma**
  - **Pinecone**
  - **Milvus**

---

##  Input & Output Specification

### Input Parameters

| Parameter     | Type | Default  |                   Description                         |
|---------------|------|----------|-------------------------------------------------------|
| `text`        | str  | Required | Raw text to embed (single sentence or large document) |
| `chunk_size`  | int  | 500      | Maximum number of characters per chunk                |

Smaller chunk sizes allow more precise retrieval at the cost of more vectors.

---

### Output Data Structure

The module returns a **list of objects**, where each object represents one text chunk.

#### Format

```json
[
  {
    "chunk_id": 0,
    "text": "The first 500 characters of your text...",
    "vector": [0.012, -0.931, 0.442, ...]
  },
  {
    "chunk_id": 1,
    "text": "...the next overlapping part of text...",
    "vector": [0.115, -0.412, 0.881, ...]
  }
]
Example vectors are 384-dimensional when using all-MiniLM models.
```

## High-Level Architecture

```text
┌───────────────┐
│   Raw Text    │
│ (User Input)  │
└───────┬───────┘
        │
        ▼
┌────────────────────┐
│ Smart Chunking     │
│ (Overlap + Limits) │
└───────┬────────────┘
        │
        ▼
┌────────────────────┐
│ Lazy Model Loader  │
│ (Load on .run())   │
└───────┬────────────┘
        │
        ▼
┌─────────────────────────────┐
│ Hardware Detection          │
│ CUDA | MPS | CPU Fallback   │
└───────┬─────────────────────┘
        │
        ▼
┌─────────────----───────┐
│     Vector Generation  │
│     (SBERT / Torch)    │
└─────----──┬────────────┘
            │
            ▼
┌──────────────────────────────┐
│ Structured Output            │
│ {chunk_id, text, vector}     │
└─────────────┬────────────────┘
              ▼
     Vector Databases (RAG)
```

## Metadata Usage Guide

- **class_name**
Tells the backend Code Generator which Python class to instantiate

- Example: EmbeddingGenerator

- **inputs**
## Used by the UI to generate a form:

text → Text Area

chunk_size → Number Input (default: 500)

- **outputs**

## type: "list_of_objects" indicates complex output

Prevents invalid connections (e.g., connecting to a node expecting a simple string)

# Python Usage Example
## Basic Usage
- from my_custom_ai_sdk.embedding import EmbeddingGenerator

### Initialize (model NOT loaded yet)
- embedder = EmbeddingGenerator(model_name="all-MiniLM-L6-v2")

### Run (model loads here → chunking → embedding)
- long_text = "Machine learning is a field of inquiry..." * 100
- results = embedder.run(long_text, chunk_size=300)

### Access results
- for item in results:
-     print(f"Chunk ID: {item['chunk_id']}")
-     print(f"Text Preview: {item['text'][:50]}...")
-     print(f"Vector Length: {len(item['vector'])}")  # e.g., 384
-     print("---")

## Integration with a Vector Database (Chroma)
- import chromadb

### Setup DB
- client = chromadb.Client()
- collection = client.create_collection("my_docs")

### Generate embeddings
- results = embedder.run(my_document_text)

### Insert into vector DB
- collection.add(
-     ids=[str(item["chunk_id"]) for item in results],
-     documents=[item["text"] for item in results],
-     embeddings=[item["vector"] for item in results] )
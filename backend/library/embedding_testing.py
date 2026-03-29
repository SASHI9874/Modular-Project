import os
import sys

# Set environment
os.environ["EMBEDDING_PROVIDER"] = "gemini"
os.environ["GOOGLE_API_KEY"] ="AIzaSyBSBeISYRZ5aFlvTEOxJ3y-2bH10jRediU"

# Add to path
sys.path.insert(0, "ai-builder-backend/library")

from embeddings_universal.runtime.adapter import run

print("🧪 Testing Embeddings Adapter\n")

# Test 1: Single text embedding
context = {
    "node_config": {
        "provider": "gemini",
        "model": "gemini-embedding-001"
    }
}
print("=" * 50)
print("TEST 1: Single Text Embedding")
print(context)
print("=" * 50)
result = run(
    inputs={"text": "Hello, this is a test"},
    context=context
)

print(f"Success: {result['success']}")
print(f"Dimension: {result.get('dimension', 'N/A')}")
print(f"Vector preview: {result.get('vector', [])[:5]}")

# Test 2: Batch embedding
print("\n" + "=" * 50)
print("TEST 2: Batch Text Embedding")
print("=" * 50)

result = run(
    inputs={
        "texts": [
            "First document about AI",
            "Second document about ML",
            "Third document about DL"
        ]
    },
    context={}
)

print(f"Success: {result['success']}")
print(f"Count: {result.get('count', 0)}")
print(f"Dimension: {result.get('dimension', 'N/A')}")
print(f"Vector preview: {result.get('vector', [])[:5]}")

# Test 3: Provider info
print("\n" + "=" * 50)
print("TEST 3: Provider Info")
print("=" * 50)

result = run(
    inputs={},
    context={}
)

print(f"Info: {result.get('info', {})}")

print("\n All adapter tests completed!")
import os
import shutil
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from .errors import VectorStoreError, CollectionNotFoundError, EmbeddingMismatchError, InvalidOperationError


def _get_embeddings():
    """
    Dynamically import embeddings service.
    Tries multiple import paths to support different execution contexts.
    """
    try:
        # Try backend library context
        from library.embeddings_universal.core.service import get_embeddings_model
        return get_embeddings_model()
    except ImportError:
        try:
            # Try generated app context
            from features.embeddings_universal.service import get_embeddings_model
            return get_embeddings_model()
        except ImportError:
            try:
                # Try relative import
                from ...embeddings_universal.core.service import get_embeddings_model
                return get_embeddings_model()
            except ImportError:
                raise ImportError(
                    "❌ embeddings-universal feature not found. "
                    "Make sure it's included in your workflow and properly configured."
                )


def _get_persist_dir(collection_name: str = "default") -> str:
    """
    Get persistent storage directory for vector DB.
    
    Priority:
    1. VECTOR_DB_PATH environment variable
    2. ~/.ai-builder/vector_dbs/
    """
    base_dir = os.getenv("VECTOR_DB_PATH")
    
    if not base_dir:
        # Default to user's home directory
        base_dir = os.path.join(
            os.path.expanduser("~"),
            ".ai-builder",
            "vector_dbs"
        )
    
    # Create collection-specific subfolder
    persist_dir = os.path.join(base_dir, collection_name)
    os.makedirs(persist_dir, exist_ok=True)
    
    return persist_dir


def _get_provider_file(collection_name: str) -> str:
    """Get path to provider metadata file"""
    return os.path.join(_get_persist_dir(collection_name), ".provider_info")


def _check_embedding_compatibility(collection_name: str, current_provider: str):
    """
    Check if collection was created with the same embedding provider.
    Prevents mixing incompatible embeddings.
    """
    provider_file = _get_provider_file(collection_name)
    
    if os.path.exists(provider_file):
        with open(provider_file, 'r') as f:
            stored_info = json.load(f)
        
        stored_provider = stored_info.get("provider")
        
        if stored_provider != current_provider:
            raise EmbeddingMismatchError(
                f"Collection '{collection_name}' was created with '{stored_provider}' embeddings, "
                f"but you're now using '{current_provider}'. "
                f"Create a new collection or switch embedding provider to match."
            )
    else:
        # Save provider info for future checks
        provider_info = {
            "provider": current_provider,
            "created_at": str(datetime.now()),
            "model": os.getenv("EMBEDDING_MODEL", "default")
        }
        
        with open(provider_file, 'w') as f:
            json.dump(provider_info, f, indent=2)


def _get_text_splitter(strategy: str = "recursive", **kwargs):
    """
    Get appropriate text splitter based on content type.
    
    Args:
        strategy: "recursive", "markdown", or "code"
        **kwargs: chunk_size, chunk_overlap, etc.
    """
    chunk_size = kwargs.get("chunk_size") or int(os.getenv("DEFAULT_CHUNK_SIZE", "1000"))
    chunk_overlap = kwargs.get("chunk_overlap") or int(os.getenv("DEFAULT_CHUNK_OVERLAP", "200"))
    
    if strategy == "recursive":
        return RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    
    elif strategy == "markdown":
        from langchain_text_splitters import MarkdownTextSplitter
        return MarkdownTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
    
    else:
        # Default to recursive
        return RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )


def index_documents(
    file_text: str,
    collection_name: str = "default",
    metadata: Optional[Dict] = None,
    chunking_strategy: str = "recursive",
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None
) -> Dict[str, Any]:
    """
    Index text into vector store.
    
    Args:
        file_text: Text content to index
        collection_name: Name of the collection
        metadata: Optional metadata to attach to documents
        chunking_strategy: Text splitting strategy
        chunk_size: Custom chunk size
        chunk_overlap: Custom chunk overlap
        
    Returns:
        Dict with indexing results
    """
    try:
        print(f"📥 [VectorStore] Indexing into collection: {collection_name}")
        
        # Get embeddings
        embeddings = _get_embeddings()
        current_provider = os.getenv("EMBEDDING_PROVIDER", "openai")
        
        # Check embedding compatibility
        _check_embedding_compatibility(collection_name, current_provider)
        
        # Get persist directory
        persist_dir = _get_persist_dir(collection_name)
        
        # Initialize vector store
        vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=embeddings,
            persist_directory=persist_dir
        )
        
        # Split text into chunks
        splitter_kwargs = {}
        if chunk_size:
            splitter_kwargs["chunk_size"] = chunk_size
        if chunk_overlap:
            splitter_kwargs["chunk_overlap"] = chunk_overlap
        
        splitter = _get_text_splitter(chunking_strategy, **splitter_kwargs)
        chunks = splitter.split_text(file_text)
        
        print(f"📄 [VectorStore] Split into {len(chunks)} chunks")
        
        # Prepare metadata
        base_metadata = metadata or {}
        base_metadata["indexed_at"] = str(datetime.now())
        base_metadata["collection"] = collection_name
        
        # Create documents with metadata
        docs = [
            Document(
                page_content=chunk,
                metadata={
                    **base_metadata,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "chunk_size": len(chunk)
                }
            )
            for i, chunk in enumerate(chunks)
        ]
        
        # Add to vector store
        vectorstore.add_documents(docs)
        
        result = {
            "status": "success",
            "chunks_indexed": len(docs),
            "collection": collection_name,
            "filename": base_metadata.get("filename", "unknown"),
            "provider": current_provider
        }
        
        print(f"✅ [VectorStore] Indexed {len(docs)} chunks successfully")
        
        return result
    
    except Exception as e:
        print(f"❌ [VectorStore] Indexing error: {str(e)}")
        raise VectorStoreError(f"Failed to index documents: {str(e)}")


def retrieve_context(
    query: str,
    collection_name: str = "default",
    k: int = 3,
    filter_metadata: Optional[Dict] = None,
    score_threshold: Optional[float] = None,
    include_sources: bool = True
) -> Dict[str, Any]:
    """
    Retrieve relevant context from vector store.
    
    Args:
        query: Search query
        collection_name: Name of the collection
        k: Number of results to retrieve
        filter_metadata: Optional metadata filters
        score_threshold: Minimum relevance score (0-1)
        include_sources: Include source metadata in output
        
    Returns:
        Dict with context and metadata
    """
    try:
        print(f"🔍 [VectorStore] Searching collection: {collection_name}")
        print(f"   Query: {query[:100]}...")
        
        # Get embeddings
        embeddings = _get_embeddings()
        persist_dir = _get_persist_dir(collection_name)
        
        # Check if collection exists
        if not os.path.exists(persist_dir):
            raise CollectionNotFoundError(f"Collection '{collection_name}' does not exist")
        
        # Initialize vector store
        vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=embeddings,
            persist_directory=persist_dir
        )
        
        # Perform search
        if score_threshold:
            results = vectorstore.similarity_search_with_relevance_scores(
                query,
                k=k,
                filter=filter_metadata
            )
            # Filter by threshold
            filtered_results = [(doc, score) for doc, score in results if score >= score_threshold]
            docs = [doc for doc, score in filtered_results]
            scores = [score for doc, score in filtered_results]
        else:
            docs = vectorstore.similarity_search(
                query,
                k=k,
                filter=filter_metadata
            )
            scores = [None] * len(docs)
        
        if not docs:
            print(f"⚠️  [VectorStore] No results found")
            return {
                "context": "",
                "num_results": 0,
                "sources": []
            }
        
        print(f"✅ [VectorStore] Found {len(docs)} relevant chunks")
        
        # Format results
        context_parts = []
        sources = []
        
        for i, (doc, score) in enumerate(zip(docs, scores)):
            source_info = {
                "filename": doc.metadata.get("filename", "Unknown"),
                "chunk_index": doc.metadata.get("chunk_index", i),
                "indexed_at": doc.metadata.get("indexed_at", "Unknown")
            }
            
            if score is not None:
                source_info["relevance_score"] = round(score, 3)
            
            sources.append(source_info)
            
            if include_sources:
                source_label = f"[Source: {source_info['filename']}]"
                if score:
                    source_label += f" (Relevance: {round(score, 2)})"
                context_parts.append(f"{source_label}\n{doc.page_content}")
            else:
                context_parts.append(doc.page_content)
        
        context = "\n\n---\n\n".join(context_parts)
        
        return {
            "context": context,
            "num_results": len(docs),
            "sources": sources,
            "collection": collection_name
        }
    
    except CollectionNotFoundError:
        raise
    except Exception as e:
        print(f"❌ [VectorStore] Retrieval error: {str(e)}")
        raise VectorStoreError(f"Failed to retrieve context: {str(e)}")


def list_collections() -> List[str]:
    """List all vector store collections"""
    try:
        base_dir = os.getenv("VECTOR_DB_PATH")
        
        if not base_dir:
            base_dir = os.path.join(
                os.path.expanduser("~"),
                ".ai-builder",
                "vector_dbs"
            )
        
        if not os.path.exists(base_dir):
            return []
        
        collections = [
            d for d in os.listdir(base_dir)
            if os.path.isdir(os.path.join(base_dir, d))
        ]
        
        return collections
    
    except Exception as e:
        print(f"❌ [VectorStore] Error listing collections: {str(e)}")
        return []


def delete_collection(collection_name: str) -> bool:
    """Delete a vector store collection"""
    try:
        persist_dir = _get_persist_dir(collection_name)
        
        if os.path.exists(persist_dir):
            shutil.rmtree(persist_dir)
            print(f"🗑️  [VectorStore] Deleted collection: {collection_name}")
            return True
        else:
            print(f"⚠️  [VectorStore] Collection not found: {collection_name}")
            return False
    
    except Exception as e:
        print(f"❌ [VectorStore] Error deleting collection: {str(e)}")
        raise VectorStoreError(f"Failed to delete collection: {str(e)}")


def get_collection_stats(collection_name: str) -> Dict[str, Any]:
    """Get statistics about a collection"""
    try:
        persist_dir = _get_persist_dir(collection_name)
        
        if not os.path.exists(persist_dir):
            raise CollectionNotFoundError(f"Collection '{collection_name}' does not exist")
        
        # Read provider info
        provider_file = _get_provider_file(collection_name)
        provider_info = {}
        
        if os.path.exists(provider_file):
            with open(provider_file, 'r') as f:
                provider_info = json.load(f)
        
        # Get embeddings and initialize vectorstore
        embeddings = _get_embeddings()
        vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=embeddings,
            persist_directory=persist_dir
        )
        
        # Get collection count
        collection = vectorstore._collection
        count = collection.count()
        
        # Calculate directory size
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(persist_dir):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                total_size += os.path.getsize(filepath)
        
        size_mb = total_size / (1024 * 1024)
        
        return {
            "name": collection_name,
            "document_count": count,
            "size_mb": round(size_mb, 2),
            "path": persist_dir,
            "provider": provider_info.get("provider", "unknown"),
            "created_at": provider_info.get("created_at", "unknown"),
            "model": provider_info.get("model", "unknown")
        }
    
    except CollectionNotFoundError:
        raise
    except Exception as e:
        print(f"❌ [VectorStore] Error getting stats: {str(e)}")
        raise VectorStoreError(f"Failed to get collection stats: {str(e)}")


def process(
    operation: str = "retrieve",
    file_text: Optional[str] = None,
    query: Optional[str] = None,
    collection_name: str = "default",
    metadata: Optional[Dict] = None,
    k: int = 3,
    **kwargs
) -> Dict[str, Any]:
    """
    Main entry point for vector store operations.
    
    Args:
        operation: "index", "retrieve", "delete", "list", or "stats"
        file_text: Text to index (for index operation)
        query: Search query (for retrieve operation)
        collection_name: Collection name
        metadata: Document metadata
        k: Number of results (for retrieve)
        **kwargs: Additional operation-specific parameters
        
    Returns:
        Operation result
    """
    try:
        if operation == "index":
            if not file_text:
                raise InvalidOperationError("file_text is required for index operation")
            
            result = index_documents(
                file_text=file_text,
                collection_name=collection_name,
                metadata=metadata,
                **kwargs
            )
            
            return {
                "result": f"✅ Indexed {result['chunks_indexed']} chunks into '{collection_name}'",
                "metadata": result
            }
        
        elif operation == "retrieve":
            if not query:
                raise InvalidOperationError("query is required for retrieve operation")
            
            result = retrieve_context(
                query=query,
                collection_name=collection_name,
                k=k,
                **kwargs
            )
            
            return {
                "result": result["context"],
                "metadata": {
                    "num_results": result["num_results"],
                    "sources": result["sources"],
                    "collection": result["collection"]
                }
            }
        
        elif operation == "list":
            collections = list_collections()
            return {
                "result": f"Found {len(collections)} collections",
                "metadata": {"collections": collections}
            }
        
        elif operation == "delete":
            success = delete_collection(collection_name)
            return {
                "result": f"✅ Deleted collection '{collection_name}'" if success else f"⚠️ Collection '{collection_name}' not found",
                "metadata": {"deleted": success}
            }
        
        elif operation == "stats":
            stats = get_collection_stats(collection_name)
            return {
                "result": f"Collection '{collection_name}': {stats['document_count']} documents ({stats['size_mb']} MB)",
                "metadata": stats
            }
        
        else:
            raise InvalidOperationError(f"Unknown operation: {operation}. Use 'index', 'retrieve', 'delete', 'list', or 'stats'")
    
    except (VectorStoreError, InvalidOperationError, CollectionNotFoundError, EmbeddingMismatchError) as e:
        return {
            "result": f"❌ Error: {str(e)}",
            "metadata": {"error": str(e), "error_type": type(e).__name__}
        }
    
    except Exception as e:
        print(f"❌ [VectorStore] Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            "result": f"❌ Unexpected error: {str(e)}",
            "metadata": {"error": str(e), "error_type": "UnexpectedError"}
        }
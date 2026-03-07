class VectorStoreError(Exception):
    """Base error for vector store operations"""
    pass


class CollectionNotFoundError(VectorStoreError):
    """Collection does not exist"""
    pass


class EmbeddingMismatchError(VectorStoreError):
    """Collection uses different embedding provider"""
    pass


class InvalidOperationError(VectorStoreError):
    """Invalid operation requested"""
    pass
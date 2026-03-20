class CodeIntelligenceError(Exception):
    """Base exception"""
    pass


class IndexNotFoundError(CodeIntelligenceError):
    """Index not found"""
    pass


class IndexingError(CodeIntelligenceError):
    """Indexing failed"""
    pass


class SearchError(CodeIntelligenceError):
    """Search failed"""
    pass
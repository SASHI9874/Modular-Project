class CodeToolsError(Exception):
    """Base exception for code tools"""
    pass


class FileNotFoundError(CodeToolsError):
    """File not found"""
    pass


class FileTooBigError(CodeToolsError):
    """File exceeds size limit"""
    pass


class PermissionError(CodeToolsError):
    """Permission denied"""
    pass


class InvalidPathError(CodeToolsError):
    """Invalid or unsafe path"""
    pass


class CommandError(CodeToolsError):
    """Command execution failed"""
    pass
class PackagerError(Exception):
    """Base packager exception"""
    pass


class GraphAnalysisError(PackagerError):
    """Error during graph analysis"""
    pass


class DependencyResolutionError(PackagerError):
    """Error resolving dependencies"""
    pass


class CodeGenerationError(PackagerError):
    """Error generating code"""
    pass


class BundlingError(PackagerError):
    """Error creating ZIP"""
    pass


class ValidationError(PackagerError):
    """Graph validation error"""
    pass


class ModeDetectionError(PackagerError):
    """Frontend mode detection error"""
    pass
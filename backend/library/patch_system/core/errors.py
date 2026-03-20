class PatchSystemError(Exception):
    """Base exception"""
    pass


class PatchGenerationError(PatchSystemError):
    """Patch generation failed"""
    pass


class PatchValidationError(PatchSystemError):
    """Patch validation failed"""
    pass


class PatchApplyError(PatchSystemError):
    """Patch apply failed"""
    pass
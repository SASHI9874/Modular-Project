from dataclasses import dataclass
from typing import Generic, TypeVar, Optional, Callable, Any

T = TypeVar('T')


@dataclass
class Result(Generic[T]):
    """Result type for error handling without exceptions"""
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    
    @staticmethod
    def ok(data: T) -> 'Result[T]':
        """Create successful result"""
        return Result(success=True, data=data)
    
    @staticmethod
    def fail(error: str, code: Optional[str] = None) -> 'Result[T]':
        """Create failed result"""
        return Result(success=False, error=error, error_code=code)
    
    def is_ok(self) -> bool:
        """Check if result is successful"""
        return self.success
    
    def is_err(self) -> bool:
        """Check if result is error"""
        return not self.success
    
    def map(self, func: Callable[[T], Any]) -> 'Result':
        """Transform data if successful"""
        if not self.success:
            return self
        try:
            return Result.ok(func(self.data))
        except Exception as e:
            return Result.fail(str(e), "MAPPING_ERROR")
    
    def unwrap(self) -> T:
        """Get data or raise exception"""
        if not self.success:
            raise ValueError(f"Cannot unwrap failed result: {self.error}")
        return self.data
    
    def unwrap_or(self, default: T) -> T:
        """Get data or return default"""
        return self.data if self.success else default
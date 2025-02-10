# src/utils/exceptions.py
class AegisException(Exception):
    """Base exception for all application-specific errors"""
    pass

class TokenLimitError(AegisException):
    """Raised when text exceeds token limit"""
    pass
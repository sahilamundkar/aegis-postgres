# src/utils/token_counter.py
import tiktoken
from functools import lru_cache
from src.config.config import get_settings

class TokenCounter:
    """
    Handles token counting for text using tiktoken.
    Uses LRU cache to improve performance for repeated calculations.
    """
    def __init__(self):
        self.encoding = tiktoken.get_encoding("cl100k_base")
        self.settings = get_settings()

    @lru_cache(maxsize=1024)
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text. Results are cached for efficiency.
        Args:
            text: Input text to count tokens for
        Returns:
            Number of tokens in text
        """
        return len(self.encoding.encode(text))

    def is_within_limit(self, text: str) -> bool:
        """
        Check if text is within token limit defined in settings.
        Args:
            text: Input text to check
        Returns:
            Boolean indicating if text is within limit
        """
        return self.count_tokens(text) <= self.settings.TOKEN_LIMIT


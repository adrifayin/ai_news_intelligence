"""
Custom Exceptions for Better Error Handling
"""


class DataStrawException(Exception):
    """Base exception for all DataStraw errors."""
    pass


class DatabaseException(DataStrawException):
    """Database operation failures."""
    pass


class APIException(DataStrawException):
    """External API failures."""
    def __init__(self, message: str, api_name: str, status_code: int = None):
        self.api_name = api_name
        self.status_code = status_code
        super().__init__(f"{api_name}: {message}")


class ValidationException(DataStrawException):
    """Data validation failures."""
    pass


class RateLimitException(APIException):
    """Rate limit exceeded."""
    def __init__(self, api_name: str, retry_after: int = None):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded", api_name, 429)


class ProcessingException(DataStrawException):
    """Data processing failures."""
    pass


class AIProcessingException(DataStrawException):
    """AI processing failures."""
    pass

from typing import Optional


class Error(Exception):
    """
    other exceptions base class
    """

    def __init__(self, message: Optional[str] = None):
        self.message = message


class ValidationError(Error):
    pass


class ResourceConflictError(Error):
    pass


class ResourceNotFound(Error):
    pass


class AuthenticationError(Error):
    pass

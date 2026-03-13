"""Shared application error types."""

class AppError(Exception):
    code = "app_error"

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

class AuthorizationError(AppError):
    code = "authorization_error"

class ValidationError(AppError):
    code = "validation_error"

class NotFoundError(AppError):
    code = "not_found"

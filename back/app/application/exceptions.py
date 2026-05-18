class ApplicationError(Exception):
    """Base application error."""


class UserAlreadyExistsError(ApplicationError):
    """Raised when a username is already registered."""


class UserNotFoundError(ApplicationError):
    """Raised when a username is not registered."""


class UnsafePromptError(ApplicationError):
    """Raised when a prompt is rejected by the local policy."""

    def __init__(self, message: str, category: str) -> None:
        super().__init__(message)
        self.category = category


class AgentUnavailableError(ApplicationError):
    """Raised when the AI agent is unavailable."""

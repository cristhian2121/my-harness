class ApplicationError(Exception):
    """Base application error."""


class UserAlreadyExistsError(ApplicationError):
    """Raised when a username is already registered."""


class UserNotFoundError(ApplicationError):
    """Raised when a username is not registered."""


class InvalidUserCredentialsError(ApplicationError):
    """Raised when a username and role combination is invalid."""


class UnsupportedDocumentFormatError(ApplicationError):
    """Raised when a document format is not supported."""


class EmptyDocumentError(ApplicationError):
    """Raised when a document upload is empty or yields no usable content."""


class DocumentProcessingError(ApplicationError):
    """Raised when document ingestion fails after upload."""


class DocumentNotFoundError(ApplicationError):
    """Raised when a document does not exist."""


class DocumentAccessError(ApplicationError):
    """Raised when a user tries to access another user's document."""


class InvalidDocumentRequestError(ApplicationError):
    """Raised when a document request payload is invalid."""


class UnsafePromptError(ApplicationError):
    """Raised when a prompt is rejected by the local policy."""

    def __init__(self, message: str, category: str) -> None:
        super().__init__(message)
        self.category = category


class AgentUnavailableError(ApplicationError):
    """Raised when the AI agent is unavailable."""

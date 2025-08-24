"""Custom exceptions for pgvector CLI."""


class PgvectorCLIError(Exception):
    """Base exception for pgvector CLI."""

    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code
        super().__init__(self.message)


class DatabaseError(PgvectorCLIError):
    """Database-related errors."""
    pass


class CollectionError(PgvectorCLIError):
    """Collection-related errors."""
    pass


class VectorError(PgvectorCLIError):
    """Vector operation errors."""
    pass


class EmbeddingError(PgvectorCLIError):
    """Embedding service errors."""
    pass


class ValidationError(PgvectorCLIError):
    """Input validation errors."""
    pass


class ConfigurationError(PgvectorCLIError):
    """Configuration errors."""
    pass

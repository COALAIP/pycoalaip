"""Custom exceptions for COALA IP.
"""


class EntityError(Exception):
    """Raised when there is an error with the entity"""


class EntityDataError(EntityError, ValueError):
    """Raised if there is an error with the entity model's data"""


class EntityNotYetPersistedError(EntityError):
    """Raised when an action requiring an entity to be available on the
    persistence layer is attempted on an entity that has not been
    persisted yet
    """

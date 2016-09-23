"""Custom exceptions for COALA IP"""


class EntityError(Exception):
    """Base class for all entity errors."""


class EntityCreationError(EntityError):
    """Raised if an error occured during the creation of an entity.
    Should contain the original error that caused the failure as the
    first argument, if available.
    """

    @property
    def error(self):
        """Original error that caused the creation of the entity on the
        persistence layer to fail
        """
        return self.args[0]


class EntityNotFoundError(EntityError):
    """Raised if the entity could not be found on the backing persistence
    layer
    """


class EntityNotYetPersistedError(EntityError):
    """Raised when an action requiring an entity to be available on the
    persistence layer is attempted on an entity that has not been
    persisted yet
    """


class EntityPreviouslyCreatedError(EntityError):
    """Raised when attempting to persist an already persisted entity.
    Should contain the existing id of the entity as the first argument.
    """

    @property
    def existing_id(self):
        """Currently existing ID of the entity on the persistence
        layer.
        """
        return self.args[0]


class ModelError(Exception):
    """Base class for all model errors."""


class ModelDataError(EntityError, ValueError):
    """Raised if there is an error with the model's data"""


class ModelNotYetLoadedError(EntityError):
    """Raised if the lazily loaded model has not been loaded from the
    backing persistence layer yet."""

"""Custom exceptions for COALA IP"""


class CoalaIpError(Exception):
    """Base class for all Coala IP errors."""


class IncompatiblePluginError(CoalaIpError, ValueError):
    """Raised when entities with incompatible plugins are used together.
    Should contain a list of the incompatible plugins as the first
    argument.
    """

    @property
    def incompatible_plugins(self):
        """:obj:`list` of :class:`~coalaip.plugin.AbstractPlugin`:
        Incompatible plugins
        """
        return self.args[0]


class ModelError(CoalaIpError):
    """Base class for all model errors."""


class ModelDataError(ModelError, ValueError):
    """Raised if there is an error with the model's data."""


class ModelNotYetLoadedError(ModelError):
    """Raised if the lazily loaded model has not been loaded from the
    backing persistence layer yet."""


class PersistenceError(CoalaIpError):
    """Base class for all persistence-related errors.

    Attributes:
        message (str): Message of the error
        error (:exc:`Exception`): Original exception, if available
    """

    def __init__(self, message='', error=None):
        self.message = message
        self.error = error

    def __str__(self):
        return self.message


class EntityCreationError(PersistenceError):
    """Raised if an error occured during the creation of an entity on the
    backing persistence layer.
    Should contain the original error that caused the failure, if
    available.
    """


class EntityNotFoundError(PersistenceError):
    """Raised if the entity could not be found on the backing persistence
    layer
    """


class EntityNotYetPersistedError(PersistenceError):
    """Raised when an action requiring an entity to be available on the
    persistence layer is attempted on an entity that has not been
    persisted yet.
    """


class EntityPreviouslyCreatedError(PersistenceError):
    """Raised when attempting to persist an already persisted entity.
    Should contain the existing id of the entity.

    Attributes:
        existing_id (str): Currently existing id of the entity on the
            persistence layer
        See :exc:`.PersistenceError` for other attributes.
    """

    def __init__(self, existing_id, *args, **kwargs):
        self.existing_id = existing_id
        super().__init__(*args, **kwargs)


class EntityTransferError(PersistenceError):
    """Raised if an error occured during the transfer of an entity on the
    backing persistence layer.
    Should contain the original error that caused the failure, if
    available.
    """

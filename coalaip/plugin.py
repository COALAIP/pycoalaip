from abc import ABC, abstractmethod, abstractproperty


class AbstractPlugin(ABC):
    """Abstract interface for all persistence layer plugins.

    Expects the following to be defined by the subclass:
        - :attr:`type` (as a read-only property)
        - :func:`generate_user`
        - :func:`get_status`
        - :func:`save`
        - :func:`transfer`
    """

    @abstractproperty
    def type(self):
        """A string denoting the type of plugin (e.g. BigchainDB)."""

    @abstractmethod
    def generate_user(self, *args, **kwargs):
        """Generate a new user on the persistence layer.

        Args:
            *args: argument list, as necessary
            **kwargs: keyword arguments, as necessary

        Returns:
            A representation of a user (e.g. a tuple with the user's
            public and private keypair) on the persistence layer
        """

    @abstractmethod
    def get_status(self, persist_id):
        """Get the status of an entity on the persistence layer.

        Args:
            persist_id (str): Id of the entity on the persistence layer

        Returns:
            Status of the entity, in any format.

        Raises:
            :exc:`~.EntityNotFoundError`: If the entity could not be
                found on the persistence layer
        """

    @abstractmethod
    def save(self, entity_data, *, user):
        """Create the entity on the persistence layer.

        Args:
            entity_data (dict): The entity's data
            user (any, keyword): The user the entity should be assigned
                to after creation. The user must be represented in the
                same format as :meth:`generate_user`'s output.

        Returns:
            str: Id of the created entity on the persistence layer

        Raises:
            :exc:`~..EntityCreationError`: If the entity failed to be
                created
        """

    @abstractmethod
    def load(self, persist_id):
        """Load the entity from the persistence layer.

        Args:
            persist_id (str): Id of the entity on the persistence layer

        Returns:
            dict: The persisted data of the entity

        Raises:
            :exc:`~.EntityNotFoundError`: If the entity could not be
                found on the persistence layer
        """

    @abstractmethod
    def transfer(self, persist_id, transfer_payload, *, from_user, to_user):
        """Transfer the entity whose id matches :attr:`persist_id` on
        the persistence layer from the current user to a new owner.

        Args:
            persist_id (str): Id of the entity on the persistence layer
            transfer_payload (dict): The transfer's payload
            from_user (any, keyword): The current owner, represented in the
                same format as :meth:`generate_user`'s output
            to_user (any, keyword): The new owner, represented in the same
                format as :meth:`generate_user`'s output

        Returns:
            str: Id of the transfer action on the persistence layer
        """

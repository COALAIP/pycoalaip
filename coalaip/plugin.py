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
        """A string denoting the type of plugin (e.g. BigchainDB)"""

    @abstractmethod
    def generate_user(self, *args, **kwargs):
        """Generate a new user on the persistence layer.

        Args:
            *args: argument list, as necessary
            **kwargs: keyword arguments, as necessary

        Returns:
            a representation of a user (e.g. a tuple with the user's
            public and private keypair) on the persistence layer
        """

    @abstractmethod
    def get_status(self, persist_id):
        """Get the status of an entity on the persistence layer.

        Args:
            persist_id (str): the id of the entity on the persistence
                layer

        Returns:
            the status of the entity, in any format.

        Raises:
            :class:`coalaip.exceptions.EntityNotFoundError`: if the
                entity could not be found on the persistence layer
        """

    @abstractmethod
    def save(self, entity_data, *, user):
        """Create the entity on the persistence layer.

        Args:
            entity_data (dict): a dict holding the entity's data
            user (, keyword): the user the entity should be assigned to
                after creation. The user should be represented in the
                same format as :meth:`generate_user`'s output.

        Returns:
            (str): the id of the created entity on the persistence layer

        Raises:
            :class:`coalaip.exceptions.EntityCreationError`: if the
                entity failed to be created
        """

    @abstractmethod
    def transfer(self, persist_id, transfer_payload, *, from_user, to_user):
        """Transfer the entity whose id matches 'persist_id' on the
        persistence layer from the current user to a new owner.

        Args:
            persist_id (str): the id of the entity on the persistence
                layer
            transfer_payload (dict): a dict holding the transfer's
                payload
            from_user (, keyword): the current owner, represented in the
                same format as :meth:`generate_user`'s output
            to_user (, keyword): the new owner, represented in the same
                format as :meth:`generate_user`'s output

        Returns:
            (str): the id of the transfer action on the persistence
            layer
        """

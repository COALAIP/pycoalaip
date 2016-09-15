"""High-level functions for interacting with COALA IP entities"""

from collections import namedtuple
from coalaip.exceptions import EntityNotYetPersistedError
from coalaip.models import Copyright, Manifestation, Work
from coalaip.plugin import AbstractPlugin


RegistrationResult = namedtuple('RegistrationResult',
                                ['copyright', 'manifestation', 'work'])


class CoalaIp:
    """High-level, plugin-bound COALA IP functions.

    Instantiated with an subclass implementing the ledger plugin
    interface (:class:`~coalaip.plugin.AbstractPlugin`) that will
    automatically be bound to all top-level functions:
        - :func:`generate_user`
        - :func:`register_manifestation`
        - :func:`derive_right`
        - :func:`transfer_right`
    """

    def __init__(self, plugin):
        """Instantiate a new CoalaIp wrapper object.

        Args:
            plugin (Plugin, keyword): the persistence layer plugin
        """

        if not isinstance(plugin, AbstractPlugin):
            raise TypeError(('A plugin subclassing '
                             "'coalaip.plugin.AbstractPlugin' must be "
                             'provided when instantiating a CoalaIp instance. '
                             'Given a plugin of type '
                             "'{}' instead.".format(type(plugin))))
        self._plugin = plugin

    def __repr__(self):
        return 'CoalaIp bound to plugin: {}'.format(self._plugin)

    def generate_user(self, *args, **kwargs):
        """Generate a new user for the backing persistence layer.

        Args:
            *args: argument list passed to the plugin's generate_user()
            **kwargs: keyword arguments passed to the plugin's
                ``generate_user()``

        Returns:
            a representation of a user, based on the persistence layer
            plugin
        """

        return self._plugin.generate_user(*args, **kwargs)

    # TODO: could probably have a 'safe' check to make sure the entities are actually created
    def register_manifestation(self, manifestation_data, *, user,
                               existing_work=None, work_data=None, **kwargs):
        """Register a Manifestation and automatically assign its
        corresponding Copyright to the given :attr:`user`.

        Unless specified (see :attr:`existing_work`), also registers a
        new Work for the Manifestation.

        Args:
            manifestation_data (dict): a dict holding the model data for
                the Manifestation.
                See :class:`~coalaip.models.Manifestation` for requirements.
            user (any, keyword): a user based on the format specified by
                the persistence layer
            existing_work (:class:`~coalaip.models.Work`, keyword, optional):
                an already persisted Work that the Manifestation is
                derived from.
                If specified, the :attr:`work_data` parameter is ignored
                and no Work is registered.
            work_data (dict, keyword, optional): a dict holding the
                model data for the Work that will automatically
                generated for the Manifestation if no existing work was
                specified.
                See :class:`~coalaip.models.Work` for requirements.
                If not specified, the Work will be created using only
                the name of the Manifestation.
            **kwargs: keyword arguments passed through to each model's
                :meth:`~coalaip.models.CoalaIpEntity.create` (e.g.
                ``data_format``).

        Returns:
            :class:`~coalaip.coalaip.RegistrationResult`: a
            :obj:`collections.namedtuple` containing the Coypright of
            the registered Manifestation, the registered Manifestation,
            and the Work (either the automatically created Work or
            the given :attr:`existing_work`) as named fields::

                (
                    'copyright': (:class:`~coalaip.models.Copyright`),
                    'manifestation': (:class:`~coalaip.models.Manifestation`),
                    'work': (:class:`~coalaip.models.Work`),
                )

        Raises:
            :class:`~coalaip.exceptions.EntityCreationError`: if the
                manifestation, its copyright, or the automatically
                created work (if no existing work is given) fail to be
                created on the persistence layer
        """

        # TODO: in the future, we may want to consider blocking (or asyncing) until
        # we confirm that an entity has actually been created

        work = existing_work
        if existing_work is None:
            if work_data is None:
                work_data = {'name': manifestation_data.get('name')}
            work = Work(work_data, plugin=self._plugin)
            work.create(user, **kwargs)
        elif not isinstance(existing_work, Work):
            raise TypeError(("'existing_work' argument to "
                             'register_manifestation() must be a Work. '
                             "Given an instance of '{}'".format(type(work))))
        elif existing_work.persist_id is None:
            raise EntityNotYetPersistedError(("Work given as 'existing_work' "
                                              'to register_manifestation() '
                                              'must be already created on the '
                                              'backing persistence layer.'))
        work_id = work.persist_id

        manifestation_data['manifestationOfWork'] = work_id
        manifestation = Manifestation(manifestation_data, plugin=self._plugin)
        manifestation.create(user, **kwargs)

        copyright_data = {'rightsOf': manifestation.persist_id}
        manifestation_copyright = Copyright(copyright_data, plugin=self._plugin)
        manifestation_copyright.create(user, **kwargs)

        return RegistrationResult(manifestation_copyright, manifestation, work)

    def derive_right(self, right_data, from_copyright, *, user,
                     data_format=None):
        """Derive a new Right from a Manifestation's Copyright.

        Args:
            right_data (dict): a dict holding the model data for the
                Right
            from_copyright (:class:`~coalaip.models.Copyright`): the id
                of the Copyright that this Right should be derived from
            user (any, keyword): a user based on the format specified by
                the persistence layer
            data_format (str, keyword, optional): the data format of the
                created Right; must be one of:
                    - 'jsonld' (default)
                    - 'json'
                    - 'ipld'

        Returns:
        """

        raise NotImplementedError('derive_right() has not been implemented yet')

    def transfer_right(self, right, rights_assignment_data, *, from_user, to_user,
                       data_format=None):
        """Transfer a Right to another user.

        Args:
            right (str): the id of the Right to transfer
            rights_assignment_data (dict): a dict holding the model data
                for the RightsAssignment
            from_user (any, keyword): a user based on the format
                specified by the persistence layer
            to_user (any, keyword): a user based on the format specified
                by the persistence layer
            data_format (str, keyword, optional): the data format of the
                saved RightsAssignment; must be one of:
                    - 'jsonld' (default)
                    - 'json'
                    - 'ipld'

        Returns:
        """

        raise NotImplementedError('transfer_right() has not been implemented yet')

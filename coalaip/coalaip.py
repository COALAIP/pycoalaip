from collections import namedtuple
from coalaip.models import Copyright, Manifestation, Work
from coalaip.plugin import AbstractPlugin


RegistrationResult = namedtuple('RegistrationResult',
                                ['copyright', 'manifestation', 'work'])


class CoalaIp:
    """Plugin-bound CoalaIP top-level functions.

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
                generate_user()

        Returns:
            a representation of a user, based on the persistence layer
                plugin
        """

        return self._plugin.generate_user(*args, **kwargs)

    # TODO: could probably have a 'safe' check to make sure the entities are actually created
    def register_manifestation(self, manifestation_data, *, user,
                               existing_work=None, work_data=None,
                               data_format=None):
        """Register a Manifestation and automatically assign its
        corresponding Copyright to the given 'user'.

        Unless specified (see 'existing_work'), also registers a new
        Work for the Manifestation.

        Args:
            manifestation_data (dict): a dict holding the model data for
                the Manifestation
            user (*, keyword): a user based on the format specified by
                the persistence layer
            existing_work (str|:class:`~coalaip.models.Work`), keyword, optional):
                the id of an already existing Work that the
                Manifestation is derived from.
                If specified, the 'work_data' parameter is ignored.
            work_data (dict, keyword, optional): a dict holding the
                model data for the Work that will automatically
                generated for the Manifestation if no existing work is
                specified.
                If not specified, the Work will be created using only the
                name of the Manifestation.
            data_format (str, keyword, optional): the data format of the
                created entities; must be one of:
                    - 'jsonld' (default)
                    - 'json'
                    - 'ipld'

        Returns:
            namedtuple: a namedtuple containing the Coypright of the
                registered Manifestation, the registered Manifestation,
                and the Work (either the automatically created Work or
                the given 'existing_work')::

                    (
                        'copyright': (:class:`~coalaip.models.Copyright`),
                        'manifestation': (:class:`~coalaip.models.Manifestation`),
                        'work': (:class:`~coalaip.models.Work`),
                    )

        Raises:
            :class:`EntityCreationError`: if the manifestation, its
                copyright, or the automatically created work (if no
                existing work is given) fail to be created on the
                persistence layer
        """

        # TODO: in the future, we may want to consider blocking (or asyncing) until
        # we confirm that an entity has actually been created

        # FIXME: is there a better way to do this? i.e. undefined in javascript
        create_kwargs = {}
        if data_format is not None:
            create_kwargs['data_format'] = data_format

        work = existing_work
        if work is None:
            if work_data is None:
                work_data = {'name': manifestation_data.get('name')}
            work = Work(work_data, plugin=self._plugin)
            work.create(user, **create_kwargs)
        elif not isinstance(work, Work):
            raise ValueError(("'existing_work' argument to "
                              'register_manifestation() must be a Work. '
                              "Given an instance of '{}'".format(type(work))))
        elif work.persist_id is not None:
            raise TypeError(("Work given as 'existing_work' argument to "
                             'register_manifestation() must have already been '
                             'created'))
        work_id = work.persist_id

        manifestation_data['manifestationOfWork'] = work_id
        manifestation = Manifestation(manifestation_data, plugin=self._plugin)
        manifestation.create(user, **create_kwargs)

        copyright_data = {'rightsOf': manifestation.persist_id}
        manifestation_copyright = Copyright(copyright_data, plugin=self._plugin)
        manifestation_copyright.create(user, **create_kwargs)

        return RegistrationResult(manifestation_copyright, manifestation, work)

    def derive_right(self, right_data, from_copyright, *, user,
                     data_format=None):
        """Derive a new Right from a Manifestation's Copyright.

        Args:
            right_data (dict): a dict holding the model data for the
                Right
            from_copyright (str): the id of the Copyright that this
                Right should be derived from
            user (*, keyword): a user based on the format specified by
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
            from_user (*, keyword): a user based on the format specified
                by the persistence layer
            to_user (*, keyword): a user based on the format specified
                by the persistence layer
            data_format (str, keyword, optional): the data format of the
                saved RightsAssignment; must be one of:
                    - 'jsonld' (default)
                    - 'json'
                    - 'ipld'

        Returns:
        """

        raise NotImplementedError('transfer_right() has not been implemented yet')

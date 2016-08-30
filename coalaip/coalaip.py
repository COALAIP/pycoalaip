from collections import namedtuple
from coalaip.models import Copyright, Manifestation, Work


RegistrationResult = namedtuple('RegistrationResult',
                                ['copyright', 'manifestation', 'work'])


# FIXME: maybe there's a better way to accomplish this?
class BoundCoalaIp:
    """Plugin-bound CoalaIP top-level functions.

    Instantiated with an subclass implementing the ledger plugin
    interface (:class:`~coalaip.plugin.AbstractPlugin`) that will
    automatically be bound to all top-level functions:
        - :func:`create_user`
        - :func:`register_manifestation`
        - :func:`derive_right`
        - :func:`transfer_right`
    """

    def __init__(self, plugin):
        # FIXME: check that plugin is instance of AbstractPlugin
        self._plugin = plugin

    def create_user(self, *args, **kwargs):
        create_user(plugin=self._plugin, *args, **kwargs)

    def register_manifestation(self, *args, **kwargs):
        register_manifestation(plugin=self._plugin, *args, **kwargs)

    def derive_right(self, *args, **kwargs):
        derive_right(plugin=self._plugin, *args, **kwargs)

    def transfer_right(self, *args, **kwargs):
        transfer_right(plugin=self._plugin, *args, **kwargs)

    def __repr__(self):
        return 'CoalaIp bound to plugin: {}'.format(self._plugin)


def bind_plugin(plugin):
    return BoundCoalaIp(plugin)


def create_user(*args, plugin, **kwargs):
    """Create a new user for the backing persistence layer.

    Args:
        plugin (Plugin, keyword): the persistence layer plugin
        *args: argument list passed to the plugin's create_user()
        **kwargs: keyword arguments passed to the plugin's create_user()

    Returns:
        a representation of a user, based on the persistence layer
            plugin
    """

    return plugin.create_user(*args, **kwargs)


def register_manifestation(manifestation_data, *, user, existing_work=None,
                           work_data=None, data_format=None, plugin):
    """Register a Manifestation and automatically assign its
    corresponding Copyright to the given 'user'.

    Unless specified (see 'existing_work'), also registers a new Work
    for the Manifestation.

    Args:
        manifestation_data (dict): a dict holding the model data for the
            Manifestation
        user (*, keyword): a user based on the format specified by the
            persistence layer
        existing_work (str|:class:`~coalaip.models.Work`), keyword, optional):
            the id of an already existing Work that the Manifestation is
            derived from.
            If specified, the 'work_data' parameter is ignored.
        work_data (dict, keyword, optional): a dict holding the model
            data for the Work that will automatically generated for the
            Manifestation if no existing work is specified.
            If not specified, the Work will be created using only the
            name of the Manifestation.
        data_format (str, keyword, optional): the data format of the
            created entities; must be one of:
                - 'jsonld' (default)
                - 'json'
                - 'ipld'
        plugin (Plugin, keyword): the persistence layer plugin

    Returns:
        namedtuple: a namedtuple containing the Coypright of the
            registered Manifestation, the registered Manifestation,
            and the Work (either the automatically created Work or the
            given 'existing_work')::

                (
                    'copyright': (:class:`~coalaip.models.Copyright`),
                    'manifestation': (:class:`~coalaip.models.Manifestation`),
                    'work': (:class:`~coalaip.models.Work`),
                )
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
        work = Work(work_data, plugin=plugin)
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

    manifestation_data['manifestationOf'] = work_id
    manifestation = Manifestation(manifestation_data, plugin=plugin)
    manifestation.create(user, **create_kwargs)

    copyright_data = {'rightsOf': manifestation.id}
    copyright = Copyright(copyright_data, plugin=plugin)
    copyright.create(user, **create_kwargs)

    return RegistrationResult(copyright, manifestation, work)


def derive_right(right_data, copyright, *, user, data_format=None, plugin):
    """Derive a new Right from a Manifestation's Copyright.

    Args:
        right_data (dict): a dict holding the model data for the Right
        copyright (str): the id of the Copyright that this Right should
            be derived from
        user (*, keyword): a user based on the format specified by the
            persistence layer
        data_format (str, keyword, optional): the data format of the
            created Right; must be one of:
                - 'jsonld' (default)
                - 'json'
                - 'ipld'
        plugin (Plugin, keyword): the persistence layer plugin

    Returns:
    """

    raise NotImplementedError('derive_right() has not been implemented yet')


def transfer_right(right, rights_assignment_data, *, from_user, to_user,
                   data_format=None, plugin):
    """Transfer a Right to another user.

    Args:
        right (str): the id of the Right to transfer
        rights_assignment_data (dict): a dict holding the model data for
            the RightsAssignment
        from_user (*, keyword): a user based on the format specified by
            the persistence layer
        to_user (*, keyword): a user based on the format specified by
            the persistence layer
        data_format (str, keyword, optional): the data format of the
            saved RightsAssignment; must be one of:
                - 'jsonld' (default)
                - 'json'
                - 'ipld'
        plugin (Plugin, keyword): the persistence layer plugin

    Returns:
    """

    raise NotImplementedError('transfer_right() has not been implemented yet')
